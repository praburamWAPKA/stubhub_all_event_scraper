#!/usr/bin/env python3
"""
StubHub Event Scraper – Explore API
=====================================
• Scrapes events by city (from worldcities.csv)
• Writes to events.csv (with buffer summary)
• Resumes from progress_log_event.log on re-run
• Shows real-time buffer count and speed per city
"""

import csv, base64, subprocess, time, json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ────── CONFIG ──────
INPUT_CSV     = "worldcities.csv"
OUT_DIR       = Path("wget_output")
COMBINED_CSV  = "events.csv"
PROGRESS_LOG  = "progress_log_event.log"
CONCURRENT    = 5
WAIT_SECS     = 1

HEADERS = [
    "-H", "Content-Type: application/x-www-form-urlencoded",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "-H", "Accept: */*",
    "-H", "Accept-Encoding: gzip, deflate",
    "-H", "Referer: https://www.stubhub.com/",
    "-H", "Origin: https://www.stubhub.com",
    "-H", "Connection: keep-alive",
]

OUT_DIR.mkdir(exist_ok=True)

def b64(s):
    return base64.b64encode(s.encode()).decode()

def load_cities():
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        return [r for r in csv.DictReader(f) if r["lat"] and r["lng"]]

def load_progress():
    progress = {}
    if Path(PROGRESS_LOG).exists():
        with open(PROGRESS_LOG, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    progress[(parts[0], parts[1])] = int(parts[2])
    return progress

def update_progress(lat, lon, page):
    with open(PROGRESS_LOG, "a", encoding='utf-8') as f:
        f.write(f"{lat},{lon},{page}\n")

def curl_url(url: str, out_file: Path) -> bool:
    cmd = ["curl", "-s", "--compressed", "-X", "GET", *HEADERS, url, "-o", str(out_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and '403' not in result.stderr

def parse_events(file_path: Path, city: str, country: str, page: int):
    try:
        content = json.loads(file_path.read_text(encoding='utf-8'))
        if content.get("events", []) == [] and content.get("total", 0) == 0:
            return None  # signal to stop scraping
        events = content.get("events", [])
        return [{
            "city": city, "country": country, "page": page,
            "eventId": e.get("eventId"), "name": e.get("name"),
            "url": e.get("url"), "venueName": e.get("venueName"),
            "formattedVenueLocation": e.get("formattedVenueLocation"),
            "categoryId": e.get("categoryId")
        } for e in events]
    except:
        return []

def save_events(rows):
    if not rows:
        return
    write_header = not Path(COMBINED_CSV).exists()
    with open(COMBINED_CSV, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

def progress_bar(events_scraped, pages_done, speed, bar_width=40):
    bar = "█" * (pages_done % bar_width) + "-" * (bar_width - (pages_done % bar_width))
    sys.stdout.write(f"\r⏳ [{bar}] {events_scraped} events across {pages_done} pages | ⏱️ {speed:.2f}/s")
    sys.stdout.flush()

def scrape_city(city_info, progress):
    city, country = city_info["name"], city_info["country"]
    lat, lon = city_info["lat"], city_info["lng"]
    lat_b64, lon_b64 = b64(lat), b64(lon)
    safe_name = city.lower().replace(" ", "_").replace("/", "_")

    start_page = progress.get((lat, lon), 0)
    total_events = 0
    start = time.time()
    page = start_page
    while True:
        out_file = OUT_DIR / f"{safe_name}_p{page}.json"
        url = f"https://www.stubhub.com/explore?method=getExploreEvents&lat={lat_b64}&lon={lon_b64}&page={page}"
        if not curl_url(url, out_file):
            break
        rows = parse_events(out_file, city, country, page)
        if rows is None:
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
        time.sleep(WAIT_SECS)
        page += 1

    elapsed_total = time.time() - start
    print(f"\n📍 {city}, {country} → {total_events} events scraped in {elapsed_total:.2f}s ({total_events / elapsed_total:.2f}/s)")

def main():
    cities = load_cities()
    progress = load_progress()
    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        futures = [pool.submit(scrape_city, c, progress) for c in cities]
        for _ in as_completed(futures):
            pass

if __name__ == "__main__":
    main()


