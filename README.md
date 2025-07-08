# 📋 StubHub Event & Venue Scraper

This project consists of two Python scripts that work together to scrape **StubHub event listings** by city and then fetch **venue seating map** data for each unique event.

---

## 📁 Contents

* `stubhub_event_scraper.py`: Scrapes event data city-by-city using the StubHub Explore API.
* `stubhub_venue_map_fetcher.py`: Fetches venue seating map data for each unique event from `events.csv`.
* `worldcities.csv`: Input city list with `name`, `country`, `lat`, and `lng` columns.
* `events.csv`: Output file containing event metadata.
* `venues/`: Output directory containing event venue JSON files.
* `progress_log_event.log`: Tracks scraping progress for resume support.

---

## ⚙️ Requirements

* Python 3.6+
* `curl` command-line tool
* Internet access
* `worldcities.csv` file in the same directory

---

## 🚀 How to Use

### ✅ Run the Scripts in This Order:

#### 1️⃣ Step 1: Scrape Events by City

Run:

```bash
python3 stubhub_event_scraper.py
```

What it does:

* Loads cities from `worldcities.csv`
* Encodes lat/lon and queries StubHub
* Scrapes paginated event data
* Saves to `events.csv`
* Resumes on re-run using `progress_log_event.log`

📆 Output:

* `wget_output/*.json` files
* `events.csv` (appended on resume)

![image](https://github.com/user-attachments/assets/2367c454-f017-42b0-ac76-0c19a7acf36d)




**Sample `events.csv` Output:**

```
city,country,page,eventId,name,url,venueName,formattedVenueLocation,categoryId
Beijing,CN,0,158266631,JJ Lin,https://www.stubhub.com/jj-lin-beijing-tickets-7-13-2025/event/158266631/,National Stadium (Bird's Nest),"Beijing, China",31461
Mumbai,IN,0,158712746,Enrique Iglesias,https://www.stubhub.com/enrique-iglesias-mumbai-tickets-10-29-2025/event/158712746/,MMRDA Grounds,"Mumbai, India",6521
Mumbai,IN,0,158488273,Enrique Iglesias,https://www.stubhub.com/enrique-iglesias-mumbai-tickets-10-30-2025/event/158488273/,MMRDA Grounds,"Mumbai, India",6521
Shanghai,CN,0,158489777,China F1 GP 2026 - Sunday Only Pass,https://www.stubhub.com/formula-1-shanghai-tickets-3-15-2026/event/158489777/,Shanghai International Circuit,"Shanghai, China",421995
Mexico City,MX,0,157403552,El Rey León,https://www.stubhub.com/the-lion-king-mexico-df-tickets-7-10-2025/event/157403552/,Teatro Telcel,"Mexico DF, Mexico",1534
Mexico City,MX,0,158098646,Ivan Cornejo,https://www.stubhub.com/ivan-cornejo-ciudad-de-mexico-tickets-7-11-2025/event/158098646/,Teatro Metropolitan,"Ciudad de México, Mexico D.F., Mexico",418875
Mexico City,MX,0,155838945,Hot Wheels Monster Trucks Live,https://www.stubhub.com/hot-wheels-monster-trucks-live-mexico-df-tickets-7-12-2025/event/155838945/,Arena CDMX,"Mexico DF, Federal District, Mexico",113112
Mexico City,MX,0,155832420,Hot Wheels Monster Trucks Live,https://www.stubhub.com/hot-wheels-monster-trucks-live-mexico-df-tickets-7-13-2025/event/155832420/,Arena CDMX,"Mexico DF, Federal District, Mexico",113112
Mexico City,MX,0,157403444,El Rey León,https://www.stubhub.com/the-lion-king-mexico-df-tickets-7-16-2025/event/157403444/,Teatro Telcel,"Mexico DF, Mexico",1534
```

---

#### 2️⃣ Step 2: Fetch Venue Map for Events

After completing event scraping, run:

```bash
python3 stubhub_venue_map_fetcher.py
```

What it does:

* Reads all unique `(eventId, categoryId)` from `events.csv`
* Makes a POST request to fetch venue seating map data
* Stores JSON per event inside `venues/`

📆 Output:

* `venues/{eventId}_venue.json` files


![image](https://github.com/user-attachments/assets/3bd03edf-520c-4fc9-b26d-4d52369a9973)

![image](https://github.com/user-attachments/assets/4aeb9589-0445-4d4e-bdad-7acca409c812)

**Sample `venue.json` Output:**

```json
{
  "1151_1176486": {
    "rows": [971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516,
              971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516, 971516,
              971516, 971516],
    "sectionId": 1176486,
    "ticketClassId": 1151,
    "sectionName": "General Admission"
  }
}
```

---

## 📊 Features

### Script 1: `stubhub_event_scraper.py`

* ✅ Resume support (`progress_log_event.log`)
* ✅ Concurrent scraping (customizable via `CONCURRENT`)
* ✅ Real-time CLI progress bar with speed
* ✅ Uses `curl` with proper headers
* ✅ Efficient event parsing and batching

### Script 2: `stubhub_venue_map_fetcher.py`

* ✅ Multi-threaded venue map downloader
* ✅ Skips already-downloaded venues
* ✅ Real-time progress bar with ETA
* ✅ Calculates speed and total time

---

## ⚙️ Configuration

### In `stubhub_event_scraper.py`:

```python
CONCURRENT = 5       # Threads for scraping cities
WAIT_SECS = 1        # Delay between page fetches
```

### In `stubhub_venue_map_fetcher.py`:

```python
CONCURRENT = 10      # Threads for venue fetch
```

---

## 📌 Notes

* Ensure your `worldcities.csv` contains valid `lat` and `lng` values.
* You can safely stop and re-run scripts. It will skip completed work.
* For large-scale scraping, consider using proxies or rotating IPs if rate-limited.

---

## 📂 Directory Structure

```
.
├── stubhub_event_scraper.py
├── stubhub_venue_map_fetcher.py
├── worldcities.csv
├── events.csv
├── progress_log_event.log
├── wget_output/
│   └── {city}_p{page}.json
└── venues/
    └── {eventId}_venue.json
```

---

## 🧑‍💻 Author

Developed by \[Your Name or GitHub Profile]

---

## 📄 License & Disclaimer

This project is provided for **educational and personal use only**.

> ⚠️ **Disclaimer:** This tool accesses public endpoints from StubHub. You are solely responsible for complying with StubHub’s [Terms of Service](https://www.stubhub.com/legal/) and any applicable laws in your jurisdiction. The authors of this tool are not liable for any misuse or consequences of its use.
