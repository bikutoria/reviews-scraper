"""
Google Maps Search Rankings Scraper

Searches Google Maps for each keyword and extracts the top 15 results.

Usage:
    python maps_rankings.py "keyword1, keyword2"
    python maps_rankings.py "brake service Atlanta GA, oil change Atlanta GA"
    python maps_rankings.py "brake service Atlanta GA, oil change Atlanta GA" --results 10
    python maps_rankings.py "brake service Atlanta GA" --headless
"""

import re
import time
import argparse
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
import pandas as pd


def get_search_results(page: Page, keyword: str, max_results: int = 15) -> list:
    """Search Google Maps for a keyword and return the top results."""
    url = f"https://www.google.com/maps/search/{urllib.parse.quote(keyword)}"
    print(f"\n[{keyword}]")
    print(f"  URL: {url}")

    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    time.sleep(3)

    # Dismiss consent/cookie dialogs if present
    for sel in [
        'button[aria-label="Accept all"]',
        'button:has-text("Accept all")',
        'form[action*="consent"] button',
    ]:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                time.sleep(2)
                break
        except Exception:
            pass

    # Wait for the results feed to appear
    try:
        page.wait_for_selector('div[role="feed"]', timeout=15000)
    except Exception:
        try:
            page.wait_for_selector('div[role="article"]', timeout=10000)
        except Exception:
            print(f"  Warning: No results found for '{keyword}'")
            return []

    time.sleep(2)

    # Scroll the results panel to load enough listings
    print(f"  Loading up to {max_results} results...")
    for _ in range(20):
        count = len(page.query_selector_all('div[role="article"]'))
        if count >= max_results:
            break
        page.evaluate('''
            (() => {
                // Prefer the dedicated feed element
                const feed = document.querySelector('div[role="feed"]');
                if (feed) { feed.scrollTop = feed.scrollHeight; return; }

                // Fallback: largest scrollable panel on the left half of the screen
                const scrollable = [...document.querySelectorAll('div')]
                    .filter(d =>
                        d.scrollHeight > d.clientHeight + 100 &&
                        d.getBoundingClientRect().left < window.innerWidth / 2
                    );
                if (scrollable.length) scrollable[0].scrollTop = scrollable[0].scrollHeight;
            })()
        ''')
        time.sleep(1.5)

    # Extract business data via JavaScript
    raw = page.evaluate('''
        (maxResults) => {
            const results = [];
            const articles = document.querySelectorAll('div[role="article"]');

            for (let i = 0; i < Math.min(articles.length, maxResults); i++) {
                const art = articles[i];

                // ── Business name ──────────────────────────────────────────────
                let name = '';
                const nameEl =
                    art.querySelector('.qBF1Pd') ||
                    art.querySelector('[class*="fontHeadline"]') ||
                    art.querySelector('[role="heading"]') ||
                    art.querySelector('h3');
                if (nameEl) name = nameEl.textContent.trim();

                // Fallback: aria-label on the card link
                if (!name) {
                    const link = art.querySelector('a[aria-label]');
                    if (link) name = link.getAttribute('aria-label') || '';
                }

                // ── Metadata rows (rating/type row, address row, etc.) ─────────
                // W4Efsd divs form the metadata block below the name.
                // We replace the bullet separator (·) with | for easier parsing.
                const metaRows = [];
                art.querySelectorAll('div.W4Efsd').forEach(div => {
                    const text = div.textContent.replace(/·/g, '|').trim();
                    if (text) metaRows.push(text);
                });

                // ── Category ───────────────────────────────────────────────────
                // Usually the last non-numeric segment in the first metadata row.
                // e.g. "4.8 | (523) | Auto Repair Shop"
                let category = '';
                if (metaRows.length > 0) {
                    const segments = metaRows[0]
                        .split('|')
                        .map(s => s.trim())
                        .filter(Boolean);
                    for (let j = segments.length - 1; j >= 0; j--) {
                        const seg = segments[j];
                        if (
                            seg.length > 1 &&
                            !/^\d/.test(seg) &&          // not a number/rating
                            !/^\(\d+\)$/.test(seg) &&    // not a count like (523)
                            !/^Open/i.test(seg) &&       // not hours
                            !/^Clos/i.test(seg) &&
                            !/^\$/.test(seg)             // not price tier
                        ) {
                            category = seg;
                            break;
                        }
                    }
                }

                // ── Address ────────────────────────────────────────────────────
                // Looks for a segment starting with a street number in rows after row 0.
                // Strips trailing hours/status text (Open, Closed, Opens, Closes, etc.)
                // that sometimes runs directly onto the address with no separator.
                let address = '';
                for (let j = 1; j < metaRows.length; j++) {
                    const segments = metaRows[j]
                        .split('|')
                        .map(s => s.trim())
                        .filter(Boolean);
                    for (const seg of segments) {
                        if (/^\d+\s+[A-Za-z]/.test(seg) && seg.length > 5) {
                            // Strip any trailing Open/Closed/Opens/Closes/hours text
                            address = seg
                                .replace(/\s*(Open|Closed|Opens|Closes|open|closed).*$/i, '')
                                .trim();
                            break;
                        }
                    }
                    if (address) break;
                }

                results.push({ name, category, address });
            }
            return results;
        }
    ''', max_results)

    rows = []
    for i, r in enumerate(raw, 1):
        name     = (r.get('name')     or '').strip()
        category = (r.get('category') or '').strip()
        address  = (r.get('address')  or '').strip()

        parts    = [p for p in [name, category, address] if p]
        business = ' - '.join(parts) if parts else name

        print(f"  #{i}: {business}")
        rows.append({
            'Keyword':  keyword,
            'Rank':     i,
            'Business': business,
        })

    return rows


def export_to_excel(rows: list) -> str:
    """Write results to a timestamped Excel file."""
    df = pd.DataFrame(rows, columns=['Keyword', 'Rank', 'Business'])

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    filename  = f"maps_rankings_{timestamp}.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rankings')
        ws = writer.sheets['Rankings']
        # Auto-size columns (cap Business column at 80 chars wide)
        col_widths = {'A': 40, 'B': 8, 'C': 80}
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width

    return filename


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Google Maps search result rankings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python maps_rankings.py "engine oil change atlanta"
  python maps_rankings.py "brake service Atlanta GA, oil change Atlanta GA"
  python maps_rankings.py "brake service Atlanta GA, oil change Atlanta GA" --results 10
  python maps_rankings.py "brake service Atlanta GA" --headless
        '''
    )
    parser.add_argument('keywords',
                        help='Comma-separated search keywords')
    parser.add_argument('--results', type=int, default=15,
                        help='Max results per keyword (default: 15)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    print(f"Keywords ({len(keywords)}): {', '.join(keywords)}")
    print(f"Max results per keyword: {args.results}")

    all_rows = []

    with sync_playwright() as p:
        # Persistent profile avoids repeated sign-in / consent flows
        context = p.chromium.launch_persistent_context(
            '/tmp/playwright-maps-search-profile',
            headless=args.headless,
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
            args=['--disable-blink-features=AutomationControlled'],
        )
        page = context.new_page()

        # Remove webdriver flag to reduce bot detection
        page.add_init_script('''
            delete navigator.__proto__.webdriver;
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        ''')

        for idx, keyword in enumerate(keywords):
            rows = get_search_results(page, keyword, args.results)
            all_rows.extend(rows)

            # Polite pause between searches (skip after the last one)
            if idx < len(keywords) - 1:
                time.sleep(3)

        context.close()

    if not all_rows:
        print("\nNo results collected.")
        return

    filename = export_to_excel(all_rows)
    print(f"\nDone. Exported {len(all_rows)} rows to: {filename}")


if __name__ == '__main__':
    main()
