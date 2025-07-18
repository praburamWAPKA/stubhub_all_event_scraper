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

* Python 3.7+ (with type hints support)
* `curl` command-line tool
* Internet access
* `worldcities.csv` file in the same directory

## 🔧 Installation

1. **Clone or download** this repository
2. **Copy configuration** (optional):
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```
3. **Test the setup**:
   ```bash
   python3 test_scraper.py
   ```

No external Python packages required! This project uses only the Python standard library.

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

### 🚀 Enhanced Script 1: `stubhub_event_scraper.py`

* ✅ **Resume support** with progress logging
* ✅ **Concurrent scraping** with configurable thread count
* ✅ **Real-time progress bars** with speed metrics
* ✅ **Robust error handling** with retry logic and exponential backoff
* ✅ **Input validation** for city data (lat/lng validation)
* ✅ **Type hints** for better code documentation
* ✅ **Structured logging** with configurable levels
* ✅ **Environment-based configuration** 
* ✅ **Graceful failure handling** and comprehensive error messages

### 🎯 Enhanced Script 2: `stubhub_venue_map_fetcher.py`

* ✅ **Multi-threaded venue downloading** with progress tracking
* ✅ **Smart skipping** of already-downloaded venues
* ✅ **Real-time progress bars** with ETA and speed calculations
* ✅ **Retry logic** for failed venue fetches
* ✅ **Data validation** for event IDs and category IDs
* ✅ **Type hints** and comprehensive error handling
* ✅ **Detailed logging** with success/failure tracking
* ✅ **Request timeouts** and connection management

### 🔧 New: `config.py`

* ✅ **Centralized configuration** management
* ✅ **Environment variable support** with fallback defaults
* ✅ **Configuration validation** with type checking
* ✅ **Flexible settings** for performance tuning

### 🧪 New: `test_scraper.py`

* ✅ **Automated testing** for core functionality
* ✅ **Configuration validation** tests
* ✅ **Utility function testing** (base64, validation, etc.)
* ✅ **JSON/CSV handling** verification
* ✅ **Retry logic testing**

---

## ⚙️ Configuration

The scraper now supports flexible configuration through:

### 🌟 Environment Variables (Recommended)
Copy `.env.example` to `.env` and customize:
```bash
# Performance settings
CONCURRENT_CITIES=5        # Cities to scrape simultaneously
CONCURRENT_VENUES=10       # Venue maps to fetch simultaneously
WAIT_SECONDS=1.0          # Delay between requests

# Retry settings
MAX_RETRIES=3             # Retry failed requests
RETRY_DELAY=2.0           # Initial retry delay (exponential backoff)
REQUEST_TIMEOUT=30        # Request timeout in seconds

# Logging
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 📝 Configuration File
All settings are centralized in `config.py` with validation and type hints.

### 🧪 Test Configuration
Run the test suite to validate your setup:
```bash
python3 test_scraper.py
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
├── stubhub_event_scraper.py      # 🚀 Enhanced event scraper
├── stubhub_venue_map_fetcher.py  # 🎯 Enhanced venue map fetcher
├── config.py                     # 🔧 Centralized configuration
├── test_scraper.py              # 🧪 Test suite
├── requirements.txt             # 📦 Dependencies (optional)
├── .env.example                 # 🌟 Environment config template
├── worldcities.csv              # 📍 Input cities data
├── top_cities.csv               # 📊 Sample city data
├── events.csv                   # 📅 Output events data
├── progress_log_event.log       # 📝 Progress tracking
├── scraper.log                  # 📋 Event scraper logs
├── venue_fetcher.log            # 📋 Venue fetcher logs
├── wget_output/                 # 📁 Raw JSON responses
│   └── {city}_p{page}.json
└── venues/                      # 🏟️ Venue map data
    └── {eventId}_venue.json
```

---

## 🧑‍💻 Author

Developed by \[Your Name or GitHub Profile]

---

## 📄 License & Disclaimer

This project is provided for **educational and personal use only**.

> ⚠️ **Disclaimer:** This tool accesses public endpoints from StubHub. You are solely responsible for complying with StubHub’s [Terms of Service](https://www.stubhub.com/legal/) and any applicable laws in your jurisdiction. The authors of this tool are not liable for any misuse or consequences of its use.
