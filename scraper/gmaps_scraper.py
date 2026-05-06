import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

from .config import get_random_delay, get_random_user_agent, HEADLESS
from .parsers import (
    parse_address,
    parse_hours_status,
    parse_google_category,
    parse_review_count,
    parse_rating,
    parse_phone,
    parse_coords_from_href,
    parse_website,
    parse_verified_badge,
)

logger = logging.getLogger(__name__)


class GoogleMapsScraperError(Exception):
    pass


class GoogleMapsScraper:
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

    async def search(self, query: str, location: str, kecamatan: str = None, kabupaten: str = None, provinsi: str = None) -> List[Dict[str, Any]]:
        """
        Search Google Maps for merchants with full location hierarchy.
        query: category name (e.g., "supermarket")
        location: kelurahan name
        kecamatan, kabupaten, provinsi: for full location precision
        Returns list of merchant data dictionaries.
        """
        start_time = time.time()
        # Build search term with full location hierarchy for precision
        if kecamatan and kabupaten and provinsi:
            search_term = f"{query} in {kecamatan}, {kabupaten}, {provinsi}"
        else:
            search_term = f"{query} in {location}"

        try:
            # Apply random delay to avoid detection
            delay = get_random_delay()
            logger.debug(f"Waiting {delay:.2f}s before search...")
            await asyncio.sleep(delay)

            # Build search URL
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

            # Wait for results to load
            await asyncio.sleep(1)

            # Try to detect if blocked (403, captcha, etc)
            page_content = await self.page.content()
            if "unusual traffic" in page_content.lower() or "captcha" in page_content.lower():
                logger.warning(f"Possible block detected for: {search_term}")
                self.stats["blocks"] += 1
                return []

            # Extract merchants from search results
            merchants = await self._extract_results(search_term)

            elapsed = time.time() - start_time
            self.stats["searches"] += 1
            self.stats["merchants_found"] += len(merchants)
            self.stats["total_time"] += elapsed

            logger.info(
                f"  Search '{search_term}': {len(merchants)} merchants in {elapsed:.2f}s"
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
        """Extract merchant data from search results page by scrolling to get all results."""
        merchants = []

        try:
            # Wait for results to appear using the correct selector
            try:
                await self.page.wait_for_selector('div.Nv2PK', timeout=5000)
            except PlaywrightTimeoutError:
                logger.debug(f"No results found for: {search_term}")
                return []

            # Scrolling to load results - keep scrolling while there's potential for more
            previous_count = 0
            scroll_attempts = 0
            max_scrolls = 200
            no_change_count = 0
            max_no_change = 50  # Keep scrolling for up to 50 attempts with no new results

            while scroll_attempts < max_scrolls and no_change_count < max_no_change:
                try:
                    # Scroll to bottom to load more results
                    await self.page.evaluate(
                        """
                        const results = document.querySelectorAll('div.Nv2PK');
                        if (results.length > 0) {
                            results[results.length - 1].scrollIntoView(true);
                        }
                        """
                    )
                    await asyncio.sleep(0.5)  # Increased wait for dynamic loading

                    # Check if we got new results
                    current_count = len(await self.page.query_selector_all('div.Nv2PK'))
                    if current_count == previous_count:
                        no_change_count += 1
                    else:
                        no_change_count = 0
                    previous_count = current_count
                    scroll_attempts += 1
                except:
                    break

            # Get all merchant elements
            elements = await self.page.query_selector_all('div.Nv2PK')

            if not elements:
                logger.debug(f"No elements found for: {search_term}")
                return []

            logger.debug(f"Found {len(elements)} merchant elements after scrolling")

            # Extract data from ALL elements (not just first 20)
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
        """Extract data from a single result element using pure parser functions."""
        try:
            merchant_data = {}

            try:
                link_elem = await element.query_selector("a[href*='/maps/place']")
                if link_elem:
                    href = await link_elem.get_attribute("href")
                    if href:
                        lat, lng = parse_coords_from_href(href)
                        if lat is not None:
                            merchant_data["lat"] = lat
                            merchant_data["lng"] = lng
            except Exception as e:
                logger.debug(f"Error extracting coords from href: {e}")

            text_content = await element.text_content()
            if not text_content:
                return None

            text = text_content.strip()
            if not text:
                return None

            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                return None

            merchant_data["name"] = lines[0]

            aria_label = await element.get_attribute("aria-label")
            if aria_label:
                merchant_data["name"] = aria_label.split("  ")[0].strip()

            rating = parse_rating(text)
            if rating is not None:
                merchant_data["rating"] = rating

            review_count = parse_review_count(text)
            if review_count is not None:
                merchant_data["review_count"] = review_count
            elif idx < 3:
                logger.debug(f"No review count found for '{lines[0]}'. Text sample: {text[:200]}")

            phone = parse_phone(text)
            if phone is not None:
                merchant_data["phone"] = phone

            website = parse_website(text)
            if website is not None:
                merchant_data["website"] = website

            verified = parse_verified_badge(text)
            if verified is not None:
                merchant_data["verified_badge"] = verified

            parts = text.split("·")
            if len(parts) >= 2:
                segment_zero = parts[0]
                addr_segment = parts[1]

                google_category = parse_google_category(segment_zero)
                if google_category is not None:
                    merchant_data["google_category"] = google_category

                hours_status = parse_hours_status(addr_segment)
                if hours_status["hours"] is not None:
                    merchant_data["hours"] = hours_status["hours"]
                    merchant_data["status"] = hours_status["status"]

                address = parse_address(addr_segment)
                if address is not None:
                    merchant_data["address"] = address

            if not merchant_data.get("name"):
                return None

            name = merchant_data["name"]
            address = merchant_data.get("address", "")
            merchant_data["google_id"] = f"gmaps_{hash((name, address)) % 10**10}"
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
