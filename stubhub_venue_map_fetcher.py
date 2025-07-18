#!/usr/bin/env python3
"""
StubHub Venue Map Fetcher – Post-processing from events.csv
===========================================================
• Reads `events.csv` and extracts unique (eventId, categoryId)
• Fetches venue map data for each and saves to JSON
• Uses parallel threads for speed
• Tracks number of successful and skipped fetches
• Displays real-time progress bar with % and buffer summary, ETA, and speed
• Shows average scraping speed and total time taken
"""

import csv
import json
import subprocess
import time
import sys
import os
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Set, Tuple, Any, Optional
from dataclasses import dataclass
from functools import wraps

# ────── CONFIGURATION ──────
@dataclass
class Config:
    """Configuration settings for the venue map fetcher."""
    events_csv: str = "events.csv"
    venue_dir: str = "venues"
    concurrent_venues: int = int(os.getenv('CONCURRENT_VENUES', 10))
    max_retries: int = int(os.getenv('MAX_RETRIES', 3))
    retry_delay: float = float(os.getenv('RETRY_DELAY', 2.0))
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', 30))

config = Config()

# ────── LOGGING SETUP ──────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('venue_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create venue directory
Path(config.venue_dir).mkdir(exist_ok=True)

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

def validate_event_data(event_id: str, category_id: str) -> bool:
    """Validate event and category IDs."""
    if not event_id or not category_id:
        logger.warning(f"Invalid event data: eventId={event_id}, categoryId={category_id}")
        return False
    
    try:
        # Basic validation - ensure they're numeric strings
        int(event_id)
        int(category_id)
        return True
    except ValueError:
        logger.warning(f"Non-numeric IDs: eventId={event_id}, categoryId={category_id}")
        return False

# ────── VENUE FETCHING FUNCTIONS ──────
@retry()
def fetch_venue_map(event_id: str, category_id: str) -> Dict[str, Any]:
    """Fetch venue map data for an event with retry logic."""
    url = f"https://www.stubhub.com/Browse/VenueMap/GetVenueMapSeatingConfig/{event_id}?categoryId={category_id}"
    cmd = [
        "curl", "-s", "--compressed", "-X", "POST", url,
        "--max-time", str(config.request_timeout),
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
        "-H", "Accept: */*",
        "-H", "Accept-Encoding: gzip, deflate",
        "-H", "Referer: https://www.stubhub.com/",
        "-H", "Origin: https://www.stubhub.com",
        "-H", "Connection: keep-alive",
        "-d", f"categoryId={category_id}&withFees=true&withSeats=false"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Curl failed with return code {result.returncode}: {result.stderr}")
    
    if not result.stdout.strip():
        raise Exception("Empty response from server")
    
    try:
        data = json.loads(result.stdout)
        logger.debug(f"Successfully fetched venue data for event {event_id}")
        return data
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {e}")

def save_venue_json(venue_map: Dict[str, Any], event_id: str) -> bool:
    """Save venue map data to JSON file."""
    if not venue_map:
        logger.warning(f"No venue data to save for event {event_id}")
        return False
    
    try:
        json_file = Path(config.venue_dir) / f"{event_id}_venue.json"
        with open(json_file, "w", encoding="utf-8") as jf:
            json.dump(venue_map, jf, indent=2)
        logger.debug(f"Saved venue data for event {event_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving venue data for event {event_id}: {e}")
        return False

def progress_bar(percent: float, count: int, total: int, elapsed: float) -> None:
    """Display real-time progress bar with ETA."""
    bar_width = 40
    filled = int(percent * bar_width / 100)
    bar = "█" * filled + "-" * (bar_width - filled)
    speed = count / elapsed if elapsed > 0 else 0
    remaining = total - count
    eta = remaining / speed if speed > 0 else 0
    mins, secs = divmod(int(eta), 60)
    
    sys.stdout.write(
        f"\r📦 [{bar}] {percent:.1f}% | {count}/{total} venues | ⏱️ {speed:.2f}/s | ETA: {mins}m {secs}s"
    )
    sys.stdout.flush()

# ────── DATA LOADING FUNCTIONS ──────
def load_unique_events() -> Set[Tuple[str, str]]:
    """Load and validate unique (eventId, categoryId) pairs from events.csv."""
    seen = set()
    invalid_count = 0
    
    try:
        with open(config.events_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                eid = row.get("eventId")
                cid = row.get("categoryId")
                
                if validate_event_data(eid, cid):
                    seen.add((eid, cid))
                else:
                    invalid_count += 1
                    logger.debug(f"Invalid event data at row {row_num}: eventId={eid}, categoryId={cid}")
        
        logger.info(f"Loaded {len(seen)} unique event/category pairs from {config.events_csv}")
        if invalid_count > 0:
            logger.warning(f"Skipped {invalid_count} invalid entries")
        
        return seen
        
    except FileNotFoundError:
        logger.error(f"Events file {config.events_csv} not found")
        raise
    except Exception as e:
        logger.error(f"Error loading events: {e}")
        raise

# ────── PROCESSING FUNCTIONS ──────
def process_event(event: Tuple[str, str], total: int, counter: Dict[str, int], start_time: float) -> None:
    """Process a single event venue fetch with progress tracking."""
    event_id, category_id = event
    
    try:
        json_path = Path(config.venue_dir) / f"{event_id}_venue.json"
        
        if json_path.exists():
            counter["skipped"] += 1
            logger.debug(f"Venue file already exists for event {event_id}")
        else:
            venue = fetch_venue_map(event_id, category_id)
            if venue and save_venue_json(venue, event_id):
                counter["success"] += 1
            else:
                counter["failed"] += 1
                logger.warning(f"Failed to fetch or save venue data for event {event_id}")
                
    except Exception as e:
        counter["failed"] += 1
        logger.error(f"Error processing event {event_id}: {e}")
    
    finally:
        counter["done"] += 1
        percent = (counter["done"] / total) * 100
        elapsed = time.time() - start_time
        progress_bar(percent, counter["done"], total, elapsed)

# ────── MAIN FUNCTION ──────
def main() -> None:
    """Main execution function."""
    try:
        logger.info("Starting StubHub venue map fetcher")
        
        # Load unique events
        unique_events = load_unique_events()
        total = len(unique_events)
        
        if total == 0:
            logger.warning("No events found to process")
            return
        
        # Initialize counters
        counter = {"done": 0, "success": 0, "skipped": 0, "failed": 0}
        
        logger.info(f"🎯 Processing {total} unique eventId/categoryId pairs with {config.concurrent_venues} workers")
        print(f"🎯 {total} unique eventId/categoryId pairs")
        
        start_time = time.time()
        
        # Process events concurrently
        with ThreadPoolExecutor(max_workers=config.concurrent_venues) as pool:
            futures = [
                pool.submit(process_event, event, total, counter, start_time) 
                for event in unique_events
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    logger.error(f"Event processing failed: {e}")
        
        # Final summary
        elapsed = time.time() - start_time
        average_speed = total / elapsed if elapsed > 0 else 0
        mins, secs = divmod(int(elapsed), 60)
        
        print(f"\n✅ Done! {counter['success']} saved, {counter['skipped']} skipped, {counter['failed']} failed")
        print(f"📊 Average processing speed: {average_speed:.2f} venues/sec")
        print(f"🕒 Total time taken: {mins}m {secs}s")
        
        logger.info(f"Venue fetching completed: {counter['success']} saved, {counter['skipped']} skipped, {counter['failed']} failed")
        logger.info(f"Average speed: {average_speed:.2f} venues/sec, Total time: {elapsed:.2f}s")
        
    except KeyboardInterrupt:
        logger.info("Venue fetching interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
