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

1. Go to Google Maps in your browser
2. Search for the business
3. Click on the **Reviews** section/tab
4. Copy the full URL from your address bar

The URL should contain the reviews parameter (`!9m1!1b1`) for best results:
```
https://www.google.com/maps/place/Business+Name/@lat,lng,17z/data=!4m8!3m7!1s...!9m1!1b1!16s...
```

Shortened URLs like `maps.app.goo.gl/...` may not work reliably.

## Lessons Learned

### Why Non-Headless Mode is Recommended

During development, we discovered that **headless mode often fails** due to Google's bot detection:

1. **Bot Detection**: Google Maps actively detects automated browsers. Headless browsers have different fingerprints that trigger detection, resulting in stripped-down pages without reviews.

2. **Dynamic Content**: Google Maps loads reviews dynamically via JavaScript. Headless mode sometimes doesn't wait long enough or execute scripts properly.

3. **Session Issues**: Subsequent headless runs after an initial successful run often fail, suggesting Google flags the browser session.

**Recommendation**: Run without `--headless` for reliable results. The browser window will open, scroll through reviews, and close automatically.

### Why Playwright?

We chose [Playwright](https://playwright.dev/) over alternatives like Selenium or Puppeteer for several reasons:

1. **Modern Architecture**: Built for modern web apps with better handling of dynamic content and SPAs like Google Maps.

2. **Auto-Wait**: Playwright automatically waits for elements to be ready, reducing flaky scripts and timing issues.

3. **Better Stealth**: More options for avoiding bot detection (custom user agents, viewport settings, JavaScript injection).

4. **Cross-Browser**: Supports Chromium, Firefox, and WebKit with a single API. We tested Firefox as a fallback for bot detection.

5. **Python-Native**: First-class Python support with synchronous and asynchronous APIs.

6. **Persistent Contexts**: Supports browser profiles that persist cookies/state across sessions, helping with bot detection.

## Troubleshooting

### "No reviews found"

1. **Check the URL**: Make sure you're using a direct business URL, not search results
2. **Try without headless**: Run without `--headless` flag
3. **Use debug mode**: Run with `--debug` to see screenshots of what the browser sees
4. **Check the reviews parameter**: URL should contain `!9m1!1b1`

### Reviews getting cut off or duplicated

The scraper automatically removes duplicates. If reviews are missing, try running with `--debug` and check `debug_page.html` for the raw page content.

### Browser crashes or timeouts

- Ensure you have enough RAM (Chromium can be memory-intensive)
- Try closing other applications
- Check your internet connection

## Limitations

- Google Maps class names change periodically; selectors may need updating
- Very large review sets (1000+) may take several minutes to scroll
- Rate limiting may occur with frequent scraping
- Bot detection can cause intermittent failures

## License

MIT
