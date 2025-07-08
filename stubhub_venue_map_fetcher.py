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

import csv, json, subprocess, time, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ────── CONFIG ──────
EVENTS_CSV   = "events.csv"
VENUE_DIR    = Path("venues")
CONCURRENT   = 10
VENUE_DIR.mkdir(exist_ok=True)

# ────── VENUE FETCHING ──────
def fetch_venue_map(event_id: str, category_id: str) -> dict:
    url = f"https://www.stubhub.com/Browse/VenueMap/GetVenueMapSeatingConfig/{event_id}?categoryId={category_id}"
    cmd = [
        "curl", "-s", "--compressed", "-X", "POST", url,
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
    try:
        return json.loads(result.stdout)
    except:
        return {}

def save_venue_json(venue_map, event_id):
    if not venue_map:
        return
    json_file = VENUE_DIR / f"{event_id}_venue.json"
    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(venue_map, jf, indent=2)

def progress_bar(percent, count, total, elapsed):
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

def process_event(event, total, counter, start_time):
    event_id, category_id = event
    json_path = VENUE_DIR / f"{event_id}_venue.json"
    if json_path.exists():
        counter["skipped"] += 1
    else:
        venue = fetch_venue_map(event_id, category_id)
        if venue:
            save_venue_json(venue, event_id)
            counter["success"] += 1
    counter["done"] += 1
    percent = (counter["done"] / total) * 100
    elapsed = time.time() - start_time
    progress_bar(percent, counter["done"], total, elapsed)

def main():
    seen = set()
    with open(EVENTS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("eventId")
            cid = row.get("categoryId")
            if eid and cid:
                seen.add((eid, cid))

    total = len(seen)
    counter = {"done": 0, "success": 0, "skipped": 0}
    print(f"🎯 {total} unique eventId/categoryId pairs")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        futures = [pool.submit(process_event, e, total, counter, start_time) for e in seen]
        for _ in as_completed(futures):
            pass

    elapsed = time.time() - start_time
    average_speed = total / elapsed if elapsed > 0 else 0
    mins, secs = divmod(int(elapsed), 60)
    print(f"\n✅ Done! {counter['success']} saved, {counter['skipped']} skipped")
    print(f"📊 Average scraping speed: {average_speed:.2f} venues/sec")
    print(f"🕒 Total time taken: {mins}m {secs}s")

if __name__ == "__main__":
    main()
