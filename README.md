# StubHub Scraper

A fast, fault‑tolerant CLI utility that harvests event data from StubHub’s *Explore* API for **every city** listed in `worldcities.csv`, combining the results into a single, tidy `events.csv`—all while automatically resuming where it left off whenever you restart the script.

---

## ✨ Key Features

| Feature                | Description                                                                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Consolidated CSV**   | Writes all events to `events.csv` with a fixed column order that’s ready for analysis in Excel, Pandas, SQL, etc.                                   |
| **Resume‑from‑log**    | Progress for each city (or a *done* flag) is appended to `progress.log`.  Restart the script anytime and it will pick up exactly where it left off. |
| **Parallel Scraping**  | Processes up to **`CONCURRENT`** cities at once using Python’s `ThreadPoolExecutor` for faster overall runtime.                                     |
| **Rate‑limit Safety**  | Adds a one‑second delay (`WAIT_SECS`) between page requests *per city* to avoid hammering the API.                                                  |
| **Out‑file Cache**     | Raw JSON from every page is stored under `wget_output/` so you can re‑parse or audit later.                                                         |
| **Thread‑safe Writes** | Exclusive locks protect both `events.csv` and `progress.log`, preventing race conditions in parallel mode.                                          |
| **403 Tip for Mobile** | Detects HTTP 403 (IP blocked) and prints an *Airplane‑mode* toggle tip—handy when running on Termux or behind a changing mobile IP.                 |
| **Max‑page Guard**     | `MAX_PAGES` caps requests per city to stay within sane limits if StubHub ever loops or paginates infinitely.                                        |
| **Empty‑page Prune**   | If a page returns an empty `"events": []`, the city is marked complete and the temporary JSON file is deleted.                                      |

---

## 🗂 File / Folder Structure

```
project/
├── stubhub_scraper.py      # ← this script
├── worldcities.csv         # Source city list (lat/lon)
├── events.csv              # ⬅️ Consolidated output (auto‑created)
├── progress.log            # ⬅️ Resume checkpoint (auto‑created)
├── wget_output/            # Raw API JSON (one file per page)
└── README.md               # ← you are here
```

---

## 🔧 Prerequisites

* **Python 3.8+**  (tested on 3.10)
* **wget** command‑line tool
* **pip packages**: `pandas`  (install via `pip install -r requirements.txt` or manually)
* A stable Internet connection 🚀

> **Tip (Linux / Termux):** Use a VPN or rotating IP address to minimise 403s.

---

## ⚙️ Configuration

Open `stubhub_scraper.py` and edit the *CONFIG* block at the top if needed:

```python
INPUT_CSV     = "worldcities.csv"   # Source of cities
OUT_DIR       = Path("wget_output") # Folder for raw JSON
COMBINED_CSV  = "events.csv"        # Final merged file
PROGRESS_LOG  = "progress.log"      # Resume checkpoint

CONCURRENT    = 5    # Parallel city workers
WAIT_SECS     = 1    # Delay between page requests
TOP_N         = None # Limit number of cities (None = all)
MAX_PAGES     = 100  # Safety limit per city
```

*For most users, the defaults are fine.*  Increase `CONCURRENT` cautiously—more threads mean more sockets (and a higher chance of getting blocked).

---

## 🚀 Quick Start

```bash
# 1. Clone or copy the repo
$ git clone https://github.com/yourname/stubhub-scraper.git
$ cd stubhub-scraper

# 2. Install Python deps
$ pip install pandas

# 3. Run the scraper
$ python stubhub_scraper.py
```

Progress is displayed in real time, for example:

```
🌍 United States, New York (start at page 0)
🔗 Fetching page 0...
✔ Saved 50 events from page 0
🔗 Fetching page 1...
...
```
![image](https://github.com/user-attachments/assets/4bead2ef-4e74-40de-b1da-36416ab5a874)

> **Interruption?** Press **Ctrl‑C** at any time. When you restart, the script uses `progress.log` to resume.

---

## ♻️ Resuming & Restarting

* **Completed cities** are tagged `done` in `progress.log`.
* **In‑progress cities** store the *next* page number to fetch.
* **Automatic cleanup**: When *all* cities show `done`, the script deletes `progress.log` and prints an *All done* message.

---

## 🛑 Handling 403 Errors

StubHub sometimes blocks an IP after \~100–150 requests. The script watches `wget`’s exit code / stderr for `403 Forbidden`:

> **Recommendation:** If you encounter a 403, it's best to run this script locally on a Unix-based system (Linux/macOS/Termux) for more control over your IP.
>
> • **On a Wi-Fi router**: Restart your router to obtain a new IP address.
>
> • **Using mobile hotspot or Termux**: Toggle airplane mode OFF and ON to get a fresh IP.

1. It prints a red ⚠️ message.
2. Suggests toggling **Airplane mode** (mobile) or reconnecting your router/VPN.
3. Continues quietly until you regain access.

*Nothing is lost—just rerun the script and it resumes automatically.*

---

## 🗃 Output Schema (`events.csv`)

| Column                                             | Meaning                                       |
| -------------------------------------------------- | --------------------------------------------- |
| city, country, page                                | Where & from which page the event was scraped |
| eventId, name, url                                 | StubHub event metadata                        |
| dayOfWeek, formattedDateWithoutYear, formattedTime | Human‑readable schedule                       |
| venueName, formattedVenueLocation, venueId         | Venue details                                 |
| categoryId, imageUrl                               | Event category & hero image                   |
| priceClass, isUnderHundred                         | Price hints                                   |
| isTbd, isDateConfirmed, isTimeConfirmed            | Date/time certainty flags                     |
| eventState, hasActiveListings, aggregateFavorites  | Live state & popularity                       |
| isFavorite, isParkingEvent, isRefetchedGlobalEvent | Misc flags                                    |

The columns are **always in the same order**, perfect for Pandas `df = pd.read_csv("events.csv")`.

---

## 🛠 Customisation Ideas

* **Rotate Proxies** – Feed a list of proxies to `wget` via `--execute use_proxy=yes`.
* **Change Headers** – Edit the `HEADERS` list for a different browser fingerprint.
* **Alternative Downloader** – Swap `wget` for `curl` or `requests` if you prefer.
* **Database Sink** – Stream parsed rows straight to Postgres/MySQL instead of a CSV.

---

## 🤖 Troubleshooting

| Symptom                                        | Cause / Fix                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| `ERROR 403: Forbidden`                         | IP blocked – change IP, wait 15–20 min, then restart.              |
| `No such file or directory: 'worldcities.csv'` | Ensure the CSV is in the script folder.                            |
| Hangs at startup                               | Check Internet; DNS or network issue.                              |
| Too slow                                       | Increase `CONCURRENT` or decrease `WAIT_SECS`, but risk more 403s. |

---

## 📄 License

MIT – do what you want, but don’t sue the author.

---

## ⚠️ Disclaimer

This script is provided for educational and research purposes only. The developer is **not responsible** for any misuse, damages, or violations of any service’s terms of use, including StubHub. Use at your own risk.

---

## 🙌 Acknowledgements

* [StubHub](https://www.stubhub.com/) – for the data (respect their ToS).
* *worldcities.csv* by SimpleMaps – city lat/lon dataset.

> Pull requests welcome!  Happy scraping.
