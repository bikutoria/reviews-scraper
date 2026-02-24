"""
Google Maps Review Scraper using Playwright
Scrapes all reviews from a Google Maps location URL and exports to Excel.
"""

import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
import pandas as pd


def scroll_reviews_panel(page: Page, max_scrolls: int = 200) -> int:
    """
    Scroll through the reviews panel to load all reviews.
    Returns the total number of reviews loaded.
    """
    previous_count = 0
    scroll_count = 0
    no_change_count = 0

    while scroll_count < max_scrolls:
        # Count current reviews using multiple possible selectors
        reviews = page.query_selector_all('div[data-review-id], div.jftiEf, div[class*="jftiEf"]')
        current_count = len(reviews)

        if current_count == previous_count:
            no_change_count += 1
            if no_change_count >= 5:
                break
        else:
            no_change_count = 0
            previous_count = current_count

        # Scroll the left sidebar panel using JavaScript
        # Try multiple possible container selectors
        page.evaluate('''
            // Find all scrollable elements and scroll the one that contains reviews or main content
            const containers = [
                document.querySelector('[role="main"] [class*="m6QErb"]'),
                document.querySelector('div.m6QErb.DxyBCb.kA9KIf.dS8AEf'),
                document.querySelector('div.m6QErb.DxyBCb'),
                document.querySelector('div.m6QErb.WNBkOb'),
                document.querySelector('div[class*="m6QErb"][class*="XiKgde"]'),
                ...document.querySelectorAll('div[class*="m6QErb"]')
            ];

            for (const container of containers) {
                if (container && container.scrollHeight > container.clientHeight) {
                    container.scrollTop = container.scrollHeight;
                    break;
                }
            }
        ''')

        time.sleep(0.8)
        scroll_count += 1
        if scroll_count % 10 == 0:
            print(f"Scroll {scroll_count}: {current_count} reviews loaded")

    return previous_count


def expand_all_reviews(page: Page):
    """Click 'More' buttons to expand truncated review text."""
    # Multiple possible selectors for the "More" button
    selectors = [
        'button[aria-label="See more"]',
        'button.w8nwRe.kyuRq',
        'button[jsaction*="pane.review.expandReview"]'
    ]

    for selector in selectors:
        buttons = page.query_selector_all(selector)
        for button in buttons:
            try:
                button.click()
                time.sleep(0.05)
            except:
                pass


def extract_reviews(page: Page) -> list:
    """Extract all review data from the page using JavaScript."""
    reviews_data = page.evaluate('''
        () => {
            const reviews = [];

            // Try multiple selectors for review containers
            const reviewElements = document.querySelectorAll('div[data-review-id], div.jftiEf');

            reviewElements.forEach(review => {
                // Reviewer name - try multiple selectors
                let reviewer = '';
                const nameEl = review.querySelector('div.d4r55')
                    || review.querySelector('button[data-review-id] div.d4r55')
                    || review.querySelector('.WNxzHc span');
                if (nameEl) reviewer = nameEl.textContent.trim();

                // Reviewer's total review count
                let reviewerReviewCount = 0;
                const reviewCountEl = review.querySelector('div.RfnDt')
                    || review.querySelector('.A503be span')
                    || review.querySelector('.section-review-subtitle');
                if (reviewCountEl) {
                    const countText = reviewCountEl.textContent;
                    // Match patterns like "15 reviews" or "42 reviews"
                    const match = countText.match(/(\d+)\s*review/i);
                    if (match) reviewerReviewCount = parseInt(match[1]);
                }

                // Star rating
                let stars = 0;
                const starEl = review.querySelector('span[role="img"]');
                if (starEl) {
                    const ariaLabel = starEl.getAttribute('aria-label');
                    if (ariaLabel) {
                        const match = ariaLabel.match(/(\d+)/);
                        if (match) stars = parseInt(match[1]);
                    }
                }

                // Date - try multiple selectors
                let date = '';
                const dateEl = review.querySelector('span.rsqaWe')
                    || review.querySelector('.DU9Pgb span')
                    || review.querySelector('.xRkPPb span');
                if (dateEl) date = dateEl.textContent.trim();

                // Review text - try multiple selectors
                let content = '';
                const textEl = review.querySelector('span.wiI7pd')
                    || review.querySelector('.MyEned span')
                    || review.querySelector('.Jtu6Td span');
                if (textEl) content = textEl.textContent.trim();

                // Check for owner response
                let hasOwnerResponse = false;
                const ownerResponseEl = review.querySelector('div.CDe7pd')
                    || review.querySelector('.d6SCIc')
                    || review.querySelector('[data-owner-response]')
                    || review.querySelector('.ODSEW-ShBeI-xgov2');
                if (ownerResponseEl) {
                    hasOwnerResponse = true;
                }

                // Only add if we have some data
                if (reviewer || content || stars > 0) {
                    reviews.push({
                        reviewer,
                        reviewer_reviews: reviewerReviewCount,
                        date,
                        stars,
                        content,
                        owner_response: hasOwnerResponse
                    });
                }
            });

            return reviews;
        }
    ''')

    return reviews_data


def scrape_google_maps_reviews(url: str, headless: bool = False, debug: bool = False) -> pd.DataFrame:
    """
    Main function to scrape reviews from a Google Maps URL.

    Args:
        url: Google Maps location URL
        headless: Run browser in headless mode (default: False for debugging)
        debug: Save screenshots for debugging

    Returns:
        DataFrame with columns: reviewer, date, stars, content
    """
    reviews_data = []

    with sync_playwright() as p:
        # Use persistent browser context for better anti-detection
        user_data_dir = '/tmp/playwright-chrome-profile'
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )
        page = context.new_page()

        # Stealth: remove webdriver flag
        page.add_init_script("""
            delete navigator.__proto__.webdriver;
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)

        print(f"Navigating to: {url}")
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)

        # Wait for content to load
        try:
            page.wait_for_selector('div[role="main"]', timeout=15000)
            # Wait for any dynamic content
            page.wait_for_load_state('networkidle', timeout=10000)
        except:
            print("Warning: Main content may not have loaded fully")

        time.sleep(2)

        if debug:
            page.screenshot(path='debug_1_initial.png')

        # Handle consent dialogs
        try:
            consent_buttons = [
                'button[aria-label="Accept all"]',
                'button:has-text("Accept all")',
                'button:has-text("Reject all")',
                'form[action*="consent"] button',
            ]
            for selector in consent_buttons:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    time.sleep(2)
                    break
        except:
            pass

        # Click on Reviews tab to open the reviews panel
        print("Looking for Reviews tab...")
        reviews_clicked = False

        # Try clicking on the star rating to open reviews panel
        try:
            # Method 1: Click on the star rating element (e.g., "4.9 stars")
            page.click('[aria-label*="stars"]', timeout=5000)
            reviews_clicked = True
            print("Clicked star rating to open reviews")
            time.sleep(3)
        except:
            pass

        if not reviews_clicked:
            try:
                # Method 2: Click the element that shows review count (e.g., "103 reviews")
                page.click('text=/\\d+\\s*reviews?/i', timeout=5000)
                reviews_clicked = True
                print("Clicked reviews count text")
                time.sleep(3)
            except:
                pass

        if not reviews_clicked:
            try:
                # Method 3: Click on "Reviews" tab button
                page.click('button >> text=Reviews', timeout=5000)
                reviews_clicked = True
                print("Clicked Reviews button")
                time.sleep(3)
            except:
                pass

        if not reviews_clicked:
            print("Could not find Reviews tab - trying to scroll to reviews section...")

        # After clicking, wait and then try to find reviews by scrolling the main panel
        time.sleep(2)

        # Look for "Sort" button which indicates we're in the reviews section
        try:
            sort_button = page.query_selector('button[aria-label*="Sort"], button:has-text("Sort")')
            if sort_button:
                print("Found reviews section (Sort button visible)")
        except:
            pass

        if debug:
            page.screenshot(path='debug_2_after_reviews_click.png')

        # Check if we're on a place page or search results
        place_name = page.query_selector('h1')
        if place_name:
            print(f"Place: {place_name.inner_text()}")
        else:
            print("Warning: Could not find place name - this may be a search results page")
            print("Please use a direct link to a specific business/place")

        # Scroll to load all reviews
        print("Scrolling to load all reviews...")
        total_reviews = scroll_reviews_panel(page)
        print(f"Total reviews found: {total_reviews}")

        # Expand truncated reviews
        print("Expanding review text...")
        expand_all_reviews(page)
        time.sleep(1)

        if debug:
            page.screenshot(path='debug_3_after_scroll.png')

        # Extract all reviews
        print("Extracting review data...")
        reviews_data = extract_reviews(page)

        print(f"Successfully extracted {len(reviews_data)} reviews")

        if debug and len(reviews_data) == 0:
            # Save page HTML for debugging
            html = page.content()
            with open('debug_page.html', 'w') as f:
                f.write(html)
            print("Saved page HTML to debug_page.html")

        context.close()

    df = pd.DataFrame(reviews_data)
    # Remove duplicate rows
    df = df.drop_duplicates()
    return df


def export_to_excel(df: pd.DataFrame, base_filename: str = "reviews") -> str:
    """
    Export DataFrame to Excel with timestamp in filename.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    filename = f"{base_filename}_{timestamp}.xlsx"

    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Exported to: {filename}")
    return filename


def main():
    """Main entry point for the scraper."""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Google Maps reviews')
    parser.add_argument('url', help='Google Maps location URL (must be a specific place, not search results)')
    parser.add_argument('--output', '-o', default='reviews',
                        help='Base filename for output (default: reviews)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    parser.add_argument('--debug', action='store_true',
                        help='Save debug screenshots')

    args = parser.parse_args()

    # Scrape reviews
    df = scrape_google_maps_reviews(args.url, headless=args.headless, debug=args.debug)

    if not df.empty:
        # Export to Excel
        export_to_excel(df, args.output)

        # Print summary
        print("\n--- Summary ---")
        print(f"Total reviews: {len(df)}")
        if df['stars'].sum() > 0:
            print(f"Average rating: {df['stars'].mean():.2f}")
        print(f"\nSample data:")
        print(df.head())
    else:
        print("No reviews found.")
        print("\nTips:")
        print("1. Make sure the URL is for a specific place, not search results")
        print("2. The URL should look like: https://www.google.com/maps/place/Business+Name/...")
        print("3. Try running without --headless to see what's happening")
        print("4. Use --debug to save screenshots for troubleshooting")


if __name__ == "__main__":
    main()
