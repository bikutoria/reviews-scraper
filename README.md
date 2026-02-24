# Google Maps Review Scraper

A Python scraper that extracts all reviews from a Google Maps business listing and exports them to Excel with timestamps.

## Features

- Scrapes all reviews from any Google Maps business page
- Extracts: reviewer name, review count, date, star rating, review content, owner response status
- Auto-scrolls to load all reviews (handles dynamic loading)
- Exports to Excel with timestamp (`reviews_YYYY-MM-DD-HH-MM.xlsx`)
- Removes duplicate entries automatically

## Output Columns

| Column | Description |
|--------|-------------|
| `reviewer` | Name of the reviewer |
| `reviewer_reviews` | Total reviews this person has posted |
| `date` | When the review was posted (relative, e.g., "2 months ago") |
| `stars` | Star rating (1-5) |
| `content` | Full review text |
| `owner_response` | `True` if owner replied, `False` otherwise |

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Install Playwright browser
python3 -m playwright install chromium
```

## Usage

```bash
python3 scraper.py "GOOGLE_MAPS_URL"
```

### Options

| Flag | Description |
|------|-------------|
| `--headless` | Run without browser window (not recommended, see below) |
| `--debug` | Save screenshots for troubleshooting |
| `-o NAME` | Custom output filename (default: `reviews`) |

### Examples

```bash
# Basic usage (recommended - opens visible browser)
python3 scraper.py "https://www.google.com/maps/place/..."

# With custom output name
python3 scraper.py "https://www.google.com/maps/place/..." -o my_business

# Headless mode (may fail due to bot detection)
python3 scraper.py "https://www.google.com/maps/place/..." --headless

# Debug mode (saves screenshots)
python3 scraper.py "https://www.google.com/maps/place/..." --debug
```

## Important: Getting the Right URL

**Use the full Google Maps URL, not shortened links.**

1. Open the business in Google Maps
2. Click the **Reviews** tab
3. Copy the full URL (should contain `!9m1!1b1`)

Shortened `maps.app.goo.gl/...` links won't work reliably.

---

## Key Insights

### Don't use headless mode

Google detects headless browsers and serves stripped-down pages without reviews. **Run without `--headless`** — the browser opens, scrolls, and closes automatically.

### Why Playwright over Selenium?

| Playwright | Selenium |
|------------|----------|
| Auto-waits for elements | Manual waits needed |
| Better bot detection evasion | Easily fingerprinted |
| Built for modern SPAs | Built for older web apps |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No reviews found | Remove `--headless`, check URL has `!9m1!1b1` |
| Reviews duplicated | Already handled — auto-deduped |
| Browser crashes | Close other apps, check RAM |

---

## Limitations

- Google may change class names (selectors need updates)
- 1000+ reviews = several minutes of scrolling
- Bot detection can cause intermittent failures

## License

MIT
