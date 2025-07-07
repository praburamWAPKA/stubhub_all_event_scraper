#!/usr/bin/env python3
"""
StubHub Scraper – Consolidated CSV + Resume + Parallel
======================================================
• Scrapes StubHub's explore API by city (from worldcities.csv)
• Resumes using progress.log (lat,lon,page or done)
• Writes consolidated events.csv (thread-safe)
• Shows 403 error tip for mobile (Termux) with Airplane mode toggle
"""

import csv, base64, subprocess, time, json, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# ────── CONFIG ──────
INPUT_CSV     = "worldcities.csv"
OUT_DIR       = Path("wget_output")
COMBINED_CSV  = "events.csv"
PROGRESS_LOG  = "progress.log"

CONCURRENT    = 5          # Number of cities processed in parallel
WAIT_SECS     = 1          # Delay between pages
TOP_N         = None       # Limit cities (None = all)
MAX_PAGES     = 100        # Safety limit per city

HEADERS = [
    "--header=User-Agent: Mozilla/5.0 (Linux; Android 10; rv:123.0) Gecko/20100101 Firefox/123.0",
    "--header=Accept: application/json",
    "--header=Referer: https://www.google.com"
]

ORDERED_COLS = [
    "city", "country", "page", "eventId", "name", "url",
    "dayOfWeek", "formattedDateWithoutYear", "formattedTime",
    "venueName", "formattedVenueLocation", "categoryId", "imageUrl",
    "priceClass", "isTbd", "isDateConfirmed", "isTimeConfirmed",
    "eventState", "venueId", "hasActiveListings", "isFavorite",
    "aggregateFavorites", "isParkingEvent", "isRefetchedGlobalEvent",
    "isUnderHundred",
]

# ────── GLOBALS ──────
b64 = lambda s: base64.b64encode(s.encode()).decode()
shown_403_tip = threading.Event()
log_lock = threading.Lock()
csv_lock = threading.Lock()
completed_cities = set()

OUT_DIR.mkdir(exist_ok=True)


# ────── PROGRESS LOG ──────
def load_progress():
    progress = {}
    if not Path(PROGRESS_LOG).exists():
        return progress
    with open(PROGRESS_LOG) as f:
        for line in f:
            lat, lon, val = line.strip().split(",")
            key = (lat, lon)
            if val == "done":
                completed_cities.add(key)
            else:
                try:
                    progress[key] = int(val)
                except:
                    pass
    return progress


def update_progress(lat, lon, page=None, done=False):
    with log_lock, open(PROGRESS_LOG, "a") as f:
        if done:
            f.write(f"{lat},{lon},done\n")
            completed_cities.add((lat, lon))
        else:
            f.write(f"{lat},{lon},{page}\n")


# ────── HELPERS ──────
def load_cities():
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        rows = [r for r in rdr if r["lat"] and r["lng"]]
    return rows[:TOP_N] if TOP_N else rows


def wget_url(url: str, out_file: Path) -> bool:
    cmd = ["wget", "-q", "--server-response", "-O", str(out_file), *HEADERS, url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if " 403 " in result.stderr or result.returncode == 8:
        if not shown_403_tip.is_set():
            print(
                "\n🚫 403 Forbidden – StubHub blocked this IP.\n"
                "👉 Run inside Termux (Android) and toggle airplane mode or reboot Wi-Fi router."
            )
            shown_403_tip.set()
        return False
    return result.returncode == 0


def is_empty(file_path: Path) -> bool:
    if not file_path.exists():
        return True
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return '"events": []' in content or '"events":[]' in content


def parse_events(file: Path, city: str, country: str, page: int) -> list:
    try:
        data = json.loads(file.read_text(encoding='utf-8'))
        events = data.get("events", [])
        return [{
            "city": city, "country": country, "page": page,
            "eventId": e.get("eventId"),
            "name": e.get("name"),
            "url": e.get("url"),
            "dayOfWeek": e.get("dayOfWeek"),
            "formattedDateWithoutYear": e.get("formattedDateWithoutYear"),
            "formattedTime": e.get("formattedTime"),
            "venueName": e.get("venueName"),
            "formattedVenueLocation": e.get("formattedVenueLocation"),
            "categoryId": e.get("categoryId"),
            "imageUrl": e.get("imageUrl"),
            "priceClass": e.get("priceClass"),
            "isTbd": e.get("isTbd"),
            "isDateConfirmed": e.get("isDateConfirmed"),
            "isTimeConfirmed": e.get("isTimeConfirmed"),
            "eventState": e.get("eventState"),
            "venueId": e.get("venueId"),
            "hasActiveListings": e.get("hasActiveListings"),
            "isFavorite": e.get("isFavorite"),
            "aggregateFavorites": e.get("aggregateFavorites"),
            "isParkingEvent": e.get("isParkingEvent"),
            "isRefetchedGlobalEvent": e.get("isRefetchedGlobalEvent"),
            "isUnderHundred": e.get("isUnderHundred"),
        } for e in events]
    except Exception as e:
        print(f"⛔ Parse error {file.name}: {e}")
        return []


def save_global_csv(rows: list):
    if not rows:
        return
    with csv_lock:
        write_header = not Path(COMBINED_CSV).exists()
        with open(COMBINED_CSV, "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ORDERED_COLS)
            if write_header:
                writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in ORDERED_COLS})


# ────── SCRAPER ──────
def scrape_city(city_info: dict, progress: dict):
    city, country = city_info["name"], city_info["country"]
    lat, lon = city_info["lat"], city_info["lng"]
    key = (lat, lon)

    if key in completed_cities:
        print(f"✅ Already completed: {city}, {country}")
        return

    lat_b64, lon_b64 = b64(lat), b64(lon)
    safe_name = city.lower().replace(" ", "_").replace("/", "_")
    page = progress.get(key, 0)

    print(f"\n🌍 {country}, {city} (start at page {page})")

    while True:
        if MAX_PAGES and page >= MAX_PAGES:
            update_progress(lat, lon, done=True)
            print(f"⛔ Max pages reached for {city}")
            break

        url = f"https://www.stubhub.com/explore?method=getExploreEvents&lat={lat_b64}&lon={lon_b64}&page={page}"
        file = OUT_DIR / f"{safe_name}_p{page}.json"

        print(f"🔗 Fetching page {page}...")
        if not wget_url(url, file):
            print(f"❌ wget failed on {city} page {page}")
            break

        if is_empty(file):
            print(f"✅ No events on page {page} – done with city")
            file.unlink(missing_ok=True)
            update_progress(lat, lon, done=True)
            break

        rows = parse_events(file, city, country, page)
        save_global_csv(rows)
        update_progress(lat, lon, page + 1)
        print(f"✔ Saved {len(rows)} events from page {page}")
        page += 1
        time.sleep(WAIT_SECS)


# ────── MAIN ──────
def main():
    cities = load_cities()
    if not cities:
        print("❌ No cities in worldcities.csv")
        return

    progress = load_progress()
    print(f"🔄 Resume state loaded: {len(progress)} pending, {len(completed_cities)} completed")

    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        futures = [pool.submit(scrape_city, city, progress) for city in cities]
        for _ in as_completed(futures):
            pass

    total = len({(c["lat"], c["lng"]) for c in cities})
    if len(completed_cities) >= total:
        print(f"\n🧹 All {total} cities completed – removing progress.log")
        Path(PROGRESS_LOG).unlink(missing_ok=True)
    else:
        print(f"📝 {len(completed_cities)} / {total} cities done – will resume remaining next run")


# ────── RUN ──────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted – exiting.")
