"""Google Maps scraper for kelurahan-level searches."""
import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, TimeoutError as PlaywrightTimeoutError

# Add parent directory to path for parser imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.parsers import (
    parse_address,
    parse_hours_status,
    parse_google_category,
    parse_review_count,
    parse_rating,
    parse_phone,
    parse_coords_from_href,
)

logger = logging.getLogger(__name__)


def get_random_delay():
    import random
    return random.uniform(0.5, 3.0)


def get_random_user_agent():
    import random
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(agents)


class GoogleMapsScraperKelurahan:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.stats = {
            "searches": 0,
            "merchants_found": 0,
            "errors": 0,
            "blocks": 0,
            "total_time": 0,
        }

    async def init(self):
        """Initialize the browser."""
        logger.info("Initializing Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )
        context = await self.browser.new_context(
            user_agent=get_random_user_agent(),
            viewport={"width": 1280, "height": 720},
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(15000)
        logger.info("Browser initialized successfully")

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def search(self, query: str, kelurahan: str, kecamatan: str, kabupaten: str, provinsi: str) -> List[Dict[str, Any]]:
        """
        Search Google Maps for merchants at kelurahan level.
        Format: [query] in Kelurahan [kelurahan], Kecamatan [kecamatan], [kabupaten], [provinsi]
        """
        start_time = time.time()

        search_term = f"{query} in Kelurahan {kelurahan}, Kecamatan {kecamatan}, {kabupaten}, {provinsi}"

        try:
            delay = get_random_delay()
            logger.debug(f"Waiting {delay:.2f}s before search...")
            await asyncio.sleep(delay)

            url = f"https://www.google.com/maps/search/{search_term.replace(' ', '+')}"
            logger.debug(f"Navigating to: {url}")

            try:
                await asyncio.wait_for(
                    self.page.goto(url, wait_until="domcontentloaded", timeout=15000),
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                logger.error(f"Page load timeout for: {search_term}")
                self.stats["errors"] += 1
                return []

            await asyncio.sleep(1)

            page_content = await self.page.content()
            if "unusual traffic" in page_content.lower() or "captcha" in page_content.lower():
                logger.warning(f"Possible block detected for: {search_term}")
                self.stats["blocks"] += 1
                return []

            merchants = await self._extract_results(search_term)

            elapsed = time.time() - start_time
            self.stats["searches"] += 1
            self.stats["merchants_found"] += len(merchants)
            self.stats["total_time"] += elapsed

            logger.info(
                f"  {query:30s}: {len(merchants):3d} merchants in {elapsed:.2f}s"
            )

            return merchants

        except PlaywrightTimeoutError:
            logger.error(f"Timeout for: {search_term}")
            self.stats["errors"] += 1
            return []
        except Exception as e:
            logger.error(f"Search error for '{search_term}': {e}")
            self.stats["errors"] += 1
            return []

    async def _extract_results(self, search_term: str) -> List[Dict[str, Any]]:
        """Extract merchant data from search results page."""
        merchants = []

        try:
            try:
                await self.page.wait_for_selector('div.Nv2PK', timeout=5000)
            except PlaywrightTimeoutError:
                logger.debug(f"No results found for: {search_term}")
                return []

            previous_count = 0
            scroll_attempts = 0
            max_scrolls = 200
            no_change_count = 0

            while scroll_attempts < max_scrolls:
                try:
                    await self.page.evaluate(
                        """
                        const results = document.querySelectorAll('div.Nv2PK');
                        if (results.length > 0) {
                            results[results.length - 1].scrollIntoView(true);
                        }
                        """
                    )
                    await asyncio.sleep(0.3)

                    current_count = len(await self.page.query_selector_all('div.Nv2PK'))
                    if current_count == previous_count:
                        no_change_count += 1
                        if no_change_count >= 15:
                            break
                    else:
                        no_change_count = 0
                    previous_count = current_count
                    scroll_attempts += 1
                except:
                    break

            elements = await self.page.query_selector_all('div.Nv2PK')

            if not elements:
                logger.debug(f"No elements found for: {search_term}")
                return []

            logger.debug(f"Found {len(elements)} merchant elements after scrolling")

            for idx, element in enumerate(elements):
                try:
                    merchant_data = await self._extract_from_element(element, idx)
                    if merchant_data and merchant_data.get("name"):
                        merchants.append(merchant_data)
                except Exception as e:
                    logger.debug(f"Error extracting element {idx}: {e}")
                    continue

            return merchants

        except Exception as e:
            logger.error(f"Error extracting results for '{search_term}': {e}")
            return []

    async def _extract_from_element(self, element, idx: int) -> Optional[Dict[str, Any]]:
        """Extract full merchant data from a single element."""
        try:
            merchant_data = {}

            text_content = await element.text_content()
            if not text_content:
                return None

            text = text_content.strip()
            if not text:
                return None

            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                return None

            # Extract name from aria-label or first line
            aria_label = await element.get_attribute("aria-label")
            if aria_label:
                merchant_data["name"] = aria_label.split("  ")[0].strip()
            else:
                merchant_data["name"] = lines[0]

            # Try to get href for coordinates
            href = await element.get_attribute("href")
            if href:
                coords = parse_coords_from_href(href)
                if coords:
                    merchant_data["lat"] = coords.get("lat")
                    merchant_data["lng"] = coords.get("lng")
                merchant_data["google_id"] = href  # Store href as unique ID
            else:
                merchant_data["google_id"] = f"kel_{idx}_{hash(merchant_data['name']) % 10**10}"

            # Parse address (usually line 1 if not name)
            if len(lines) > 1:
                merchant_data["address"] = parse_address(lines[1])

            # Parse rating and review count from aria-label or lines
            if aria_label:
                rating_match = re.search(r'([0-9]\.[0-9])\s*stars?', aria_label)
                if rating_match:
                    merchant_data["rating"] = float(rating_match.group(1))

                review_match = re.search(r'\(([0-9,]+)\s*(?:review|rating)', aria_label)
                if review_match:
                    merchant_data["review_count"] = int(review_match.group(1).replace(',', ''))

            # Parse category from aria-label
            if aria_label:
                merchant_data["google_category"] = parse_google_category(aria_label)

            # Extract phone if present (usually has phone icon pattern)
            merchant_data["phone"] = ""
            merchant_data["hours"] = ""
            merchant_data["status"] = ""

            # Add timestamp
            merchant_data["scraped_at"] = datetime.now(timezone.utc).isoformat()

            return merchant_data

        except Exception as e:
            logger.debug(f"Error extracting from element: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            **self.stats,
            "avg_time_per_search": (
                self.stats["total_time"] / self.stats["searches"]
                if self.stats["searches"] > 0
                else 0
            ),
            "avg_merchants_per_search": (
                self.stats["merchants_found"] / self.stats["searches"]
                if self.stats["searches"] > 0
                else 0
            ),
        }
