#!/usr/bin/env python3
"""
StubHub Event Scraper – Explore API
=====================================
• Scrapes events by city (from worldcities.csv)
• Writes to events.csv (with buffer summary)
• Resumes from progress_log_event.log on re-run
• Shows real-time buffer count and speed per city
"""

import csv
import base64
import subprocess
import time
import json
import sys
import os
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from functools import wraps

# ────── CONFIGURATION ──────
@dataclass
class Config:
    """Configuration settings for the scraper."""
    input_csv: str = "worldcities.csv"
    out_dir: str = "wget_output"
    combined_csv: str = "events.csv"
    progress_log: str = "progress_log_event.log"
    concurrent_cities: int = int(os.getenv('CONCURRENT_CITIES', 5))
    wait_seconds: float = float(os.getenv('WAIT_SECONDS', 1.0))
    max_retries: int = int(os.getenv('MAX_RETRIES', 3))
    retry_delay: float = float(os.getenv('RETRY_DELAY', 2.0))

config = Config()

# ────── LOGGING SETUP ──────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ────── HTTP HEADERS ──────
HEADERS = [
    "-H", "Content-Type: application/x-www-form-urlencoded",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "-H", "Accept: */*",
    "-H", "Accept-Encoding: gzip, deflate",
    "-H", "Referer: https://www.stubhub.com/",
    "-H", "Origin: https://www.stubhub.com",
    "-H", "Connection: keep-alive",
]

# Create output directory
Path(config.out_dir).mkdir(exist_ok=True)

# ────── UTILITY FUNCTIONS ──────
def retry(func=None, *, max_attempts: int = None, delay: float = None):
    """Decorator to retry function calls with exponential backoff."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempts = max_attempts if max_attempts is not None else config.max_retries
            retry_delay = delay if delay is not None else config.retry_delay
            
            for attempt in range(attempts):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if attempt == attempts - 1:
                        logger.error(f"Failed after {attempts} attempts: {e}")
                        raise
                    wait_time = retry_delay * (2 ** attempt)  # exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        return wrapper
    
    if func is None:
        # Called with parameters: @retry(max_attempts=3)
        return decorator
    else:
        # Called without parameters: @retry
        return decorator(func)

def b64(s: str) -> str:
    """Encode string to base64."""
    return base64.b64encode(s.encode()).decode()

def validate_city_data(city_info: Dict[str, str]) -> bool:
    """Validate that city data contains required fields."""
    required_fields = ['name', 'country', 'lat', 'lng']
    is_valid = all(field in city_info and city_info[field] for field in required_fields)
    
    if not is_valid:
        logger.warning(f"Invalid city data: {city_info}")
        return False
    
    try:
        # Validate lat/lng are numeric
        float(city_info['lat'])
        float(city_info['lng'])
        return True
    except ValueError:
        logger.warning(f"Invalid lat/lng values for city: {city_info}")
        return False

# ────── DATA LOADING FUNCTIONS ──────
def load_cities() -> List[Dict[str, str]]:
    """Load and validate cities from CSV file."""
    try:
        with open(config.input_csv, newline='', encoding='utf-8') as f:
            cities = [r for r in csv.DictReader(f) if validate_city_data(r)]
            logger.info(f"Loaded {len(cities)} valid cities from {config.input_csv}")
            return cities
    except FileNotFoundError:
        logger.error(f"Input file {config.input_csv} not found")
        raise
    except Exception as e:
        logger.error(f"Error loading cities: {e}")
        raise

def load_progress() -> Dict[Tuple[str, str], int]:
    """Load scraping progress from log file."""
    progress = {}
    if Path(config.progress_log).exists():
        try:
            with open(config.progress_log, encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parts = line.strip().split(",")
                    if len(parts) == 3:
                        try:
                            progress[(parts[0], parts[1])] = int(parts[2])
                        except ValueError:
                            logger.warning(f"Invalid progress entry at line {line_num}: {line.strip()}")
            logger.info(f"Loaded progress for {len(progress)} cities")
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
    return progress

def update_progress(lat: str, lon: str, page: int) -> None:
    """Update progress log with completed page."""
    try:
        with open(config.progress_log, "a", encoding='utf-8') as f:
            f.write(f"{lat},{lon},{page}\n")
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

# ────── WEB SCRAPING FUNCTIONS ──────
@retry()
def curl_url(url: str, out_file: Path) -> bool:
    """Download URL content using curl with retry logic."""
    cmd = ["curl", "-s", "--compressed", "-X", "GET", *HEADERS, url, "-o", str(out_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Curl failed with return code {result.returncode}: {result.stderr}")
    
    if '403' in result.stderr:
        raise Exception("HTTP 403 Forbidden - possible rate limiting")
    
    return True

def parse_events(file_path: Path, city: str, country: str, page: int) -> Optional[List[Dict[str, Any]]]:
    """Parse events from JSON file and return structured data."""
    try:
        content = json.loads(file_path.read_text(encoding='utf-8'))
        
        # Check if we've reached the end of results
        if content.get("events", []) == [] and content.get("total", 0) == 0:
            return None  # signal to stop scraping
        
        events = content.get("events", [])
        if not events:
            logger.warning(f"No events found in {file_path}")
            return []
        
        return [{
            "city": city, 
            "country": country, 
            "page": page,
            "eventId": e.get("eventId"), 
            "name": e.get("name"),
            "url": e.get("url"), 
            "venueName": e.get("venueName"),
            "formattedVenueLocation": e.get("formattedVenueLocation"),
            "categoryId": e.get("categoryId")
        } for e in events]
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return []
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}")
        return []

def save_events(rows: List[Dict[str, Any]]) -> None:
    """Save events to CSV file."""
    if not rows:
        return
    
    try:
        write_header = not Path(config.combined_csv).exists()
        with open(config.combined_csv, "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            if write_header:
                writer.writeheader()
            writer.writerows(rows)
        logger.debug(f"Saved {len(rows)} events to {config.combined_csv}")
    except Exception as e:
        logger.error(f"Error saving events: {e}")
        raise

def progress_bar(events_scraped: int, pages_done: int, speed: float, bar_width: int = 40) -> None:
    """Display real-time progress bar."""
    bar = "█" * (pages_done % bar_width) + "-" * (bar_width - (pages_done % bar_width))
    sys.stdout.write(f"\r⏳ [{bar}] {events_scraped} events across {pages_done} pages | ⏱️ {speed:.2f}/s")
    sys.stdout.flush()

# ────── MAIN SCRAPING FUNCTION ──────
def scrape_city(city_info: Dict[str, str], progress: Dict[Tuple[str, str], int]) -> None:
    """Scrape events for a single city with progress tracking."""
    city, country = city_info["name"], city_info["country"]
    lat, lon = city_info["lat"], city_info["lng"]
    lat_b64, lon_b64 = b64(lat), b64(lon)
    safe_name = city.lower().replace(" ", "_").replace("/", "_")

    logger.info(f"Starting scrape for {city}, {country}")
    start_page = progress.get((lat, lon), 0)
    total_events = 0
    start = time.time()
    page = start_page
    
    try:
        while True:
            out_file = Path(config.out_dir) / f"{safe_name}_p{page}.json"
            url = f"https://www.stubhub.com/explore?method=getExploreEvents&lat={lat_b64}&lon={lon_b64}&page={page}"
            
            try:
                if not curl_url(url, out_file):
                    logger.warning(f"Failed to fetch page {page} for {city}")
                    break
                    
                rows = parse_events(out_file, city, country, page)
                if rows is None:
                    logger.info(f"No more events for {city} at page {page}")
                    break
                    
                if not rows:
                    page += 1
                    continue
                    
                total_events += len(rows)
                save_events(rows)

                elapsed = time.time() - start
                speed = total_events / elapsed if elapsed > 0 else 0
                progress_bar(total_events, page + 1, speed)
                update_progress(lat, lon, page + 1)
                
                time.sleep(config.wait_seconds)
                page += 1
                
            except Exception as e:
                logger.error(f"Error processing page {page} for {city}: {e}")
                break

    except Exception as e:
        logger.error(f"Fatal error scraping {city}: {e}")
    finally:
        elapsed_total = time.time() - start
        speed_final = total_events / elapsed_total if elapsed_total > 0 else 0
        logger.info(f"📍 {city}, {country} → {total_events} events scraped in {elapsed_total:.2f}s ({speed_final:.2f}/s)")
        print(f"\n📍 {city}, {country} → {total_events} events scraped in {elapsed_total:.2f}s ({speed_final:.2f}/s)")

# ────── MAIN FUNCTION ──────
def main() -> None:
    """Main execution function."""
    try:
        logger.info("Starting StubHub event scraper")
        cities = load_cities()
        progress = load_progress()
        
        logger.info(f"Processing {len(cities)} cities with {config.concurrent_cities} concurrent workers")
        
        with ThreadPoolExecutor(max_workers=config.concurrent_cities) as pool:
            futures = [pool.submit(scrape_city, c, progress) for c in cities]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    logger.error(f"City scraping failed: {e}")
        
        logger.info("Scraping completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()


