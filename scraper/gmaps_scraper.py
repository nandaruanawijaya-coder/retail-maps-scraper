import asyncio
import logging
import re
import time
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

from .config import get_random_delay, get_random_user_agent, HEADLESS

logger = logging.getLogger(__name__)


class GoogleMapsScraperError(Exception):
    pass


def parse_reviews_count_robust(text: Optional[str]) -> Optional[int]:
    """
    Robust review count extraction for formats not caught by simple regex.
    Handles: "123 reviews", "1,234", "1.234", "1 234"
    """
    if not text:
        return None

    try:
        text = str(text).strip().lower()

        # Pattern 1: "N reviews" or "N review"
        match = re.search(r'(\d+(?:[,.\s]\d+)*)\s*reviews?(?!\w)', text)
        if match:
            num_str = re.sub(r'[,.\s]', '', match.group(1))
            if num_str.isdigit():
                return int(num_str)

        # Pattern 2: "N K" (e.g., "1.2K", "1,2K") - thousands abbreviation
        match = re.search(r'(\d+(?:[,.\s]\d+)?)\s*k(?:elauan)?$', text)
        if match:
            num_str = match.group(1).replace(',', '.').replace(' ', '')
            try:
                return int(float(num_str) * 1000)
            except:
                pass

        return None
    except Exception as e:
        logger.debug(f"Error in robust parsing: {e}")
        return None


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

            # Scrolling to load results - wait for dynamic content to load
            previous_count = 0
            scroll_attempts = 0
            max_scrolls = 200
            no_change_count = 0

            while scroll_attempts < max_scrolls:
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
                    await asyncio.sleep(0.3)

                    # Check if we got new results
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
        """Extract data from a single result element, including lat/lng from href."""
        try:
            merchant_data = {}

            # Try to extract lat/lng from the merchant link href first
            try:
                link_elem = await element.query_selector("a[href*='/maps/place']")
                if link_elem:
                    href = await link_elem.get_attribute("href")
                    if href:
                        # Try pattern 1: !8m2!3d[lat]!4d[lng]
                        coords_match = re.search(r'!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', href)
                        if coords_match:
                            merchant_data["lat"] = float(coords_match.group(1))
                            merchant_data["lng"] = float(coords_match.group(2))
                        else:
                            # Try pattern 2: @[lat],[lng]
                            coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
                            if coords_match:
                                merchant_data["lat"] = float(coords_match.group(1))
                                merchant_data["lng"] = float(coords_match.group(2))
            except Exception as e:
                logger.debug(f"Error extracting coords from href: {e}")

            # Get visible text content
            text_content = await element.text_content()
            if not text_content:
                return None

            text = text_content.strip()
            if not text:
                return None

            # Extract name from element (first line usually)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                return None

            merchant_data["name"] = lines[0]

            # Get aria-label for clean name
            aria_label = await element.get_attribute("aria-label")
            if aria_label:
                merchant_data["name"] = aria_label.split("  ")[0].strip()

            # Extract rating (pattern: 4,9 or 4.9)
            rating_match = re.search(r"([\d],[\d]|[\d]\.[\d])", text)
            if rating_match:
                try:
                    rating_str = rating_match.group(1).replace(",", ".")
                    merchant_data["rating"] = float(rating_str)
                except:
                    pass

            # Extract review count - first try simple regex, then robust parsing
            review_count = None

            # Step 1: Try simple regex for (123) format
            review_match = re.search(r"\((\d+)\)", text)
            if review_match:
                try:
                    review_count = int(review_match.group(1))
                except:
                    pass

            # Step 2: If not found, try robust parsing for other formats
            if review_count is None:
                review_count = parse_reviews_count_robust(text)

            if review_count is not None:
                merchant_data["review_count"] = review_count
            else:
                # Debug: log when review count is not found
                if idx < 3:  # Only log first 3
                    logger.debug(f"No review count found for '{lines[0]}'. Text sample: {text[:200]}")

            # Extract phone number (pattern: 0XXXX-XXXX-XXXX or +62 or 0 followed by digits)
            phone_match = re.search(r"(0\d{7,}|\+62\d{8,}|\d{3,4}-\d{3,4}-\d{3,4})", text)
            if phone_match:
                merchant_data["phone"] = phone_match.group(1)

            # Extract address (between · separators)
            parts = text.split("·")
            if len(parts) >= 2:
                addr_part = parts[1].strip()
                # Clean merged text like "noBuka" -> "Buka"
                addr_part = re.sub(r'no([A-Z])', r' \1', addr_part)
                # Remove trailing keywords
                addr_part = re.sub(r'(Situs Web|Rute|Tel|\.\.\.)', '', addr_part).strip()
                if addr_part and len(addr_part) > 3:
                    merchant_data["address"] = addr_part


            # Check if we have a valid name
            if not merchant_data.get("name"):
                return None

            # Generate a unique ID
            name = merchant_data["name"]
            address = merchant_data.get("address", "")
            merchant_data["google_id"] = f"gmaps_{hash((name, address)) % 10**10}"

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
