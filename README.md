# Google Maps Scrapers

Two Python scrapers for Google Maps, both built with Playwright and exporting to Excel.

---

## 1. Search Rankings Scraper — `maps_rankings.py`

Takes a list of keywords, searches Google Maps for each one, and records the top 15 results with their rank, business name, type, and address.

### Output

File: `maps_rankings_YYYY-MM-DD-HH-MM.xlsx`

| Column | Description |
|--------|-------------|
| `Keyword` | The search term used |
| `Rank` | Position in Google Maps results (1–15) |
| `Business` | Business name, type, and address combined (e.g. `Midas - Auto Repair - 920 Northside Dr NW`) |

### Usage

```bash
# Single keyword
python3 maps_rankings.py "brake service Atlanta GA"

# Multiple keywords (comma-separated)
python3 maps_rankings.py "brake service Atlanta GA, engine oil change Atlanta, car AC repair Atlanta"

# Change number of results (default: 15)
python3 maps_rankings.py "oil change Atlanta" --results 10

# Headless mode (not recommended — see note below)
python3 maps_rankings.py "oil change Atlanta" --headless
```

---

## 2. Review Scraper — `scraper.py`

Scrapes all reviews from a specific Google Maps business listing.

### Output

File: `BusinessName_reviews_YYYY-MM-DD-HH-MM.xlsx`

| Column | Description |
|--------|-------------|
| `reviewer` | Name of the reviewer |
| `reviewer_reviews` | Total reviews this person has posted |
| `date` | When the review was posted (e.g. "2 months ago") |
| `stars` | Star rating (1–5) |
| `content` | Full review text |
| `owner_response` | `True` if the owner replied, `False` otherwise |

### Usage

```bash
# Basic usage
python3 scraper.py "https://www.google.com/maps/place/..."

# With custom output name
python3 scraper.py "https://www.google.com/maps/place/..." -o my_business

# Debug mode (saves screenshots)
python3 scraper.py "https://www.google.com/maps/place/..." --debug
```

**Getting the right URL:** Open the business in Google Maps, click the Reviews tab, and copy the full URL. It should contain `!9m1!1b1`. Shortened `maps.app.goo.gl/...` links won't work reliably.

---

## Installation

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

---

## Notes

- **Don't use `--headless`** — Google detects headless browsers and serves stripped-down pages. The browser opens, runs, and closes automatically.
- Google may change class names over time, which can require selector updates.
- Bot detection can cause intermittent failures; a short wait and retry usually resolves it.

## License

MIT
