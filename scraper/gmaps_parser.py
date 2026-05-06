import logging
import json
import re
from typing import Optional

logger = logging.getLogger(__name__)


class GoogleMapsParser:
    """Parse raw Google Maps merchant data into standardized format."""

    def parse_merchant(
        self, raw_data: dict, category: dict, district
    ) -> Optional[dict]:
        """Convert raw Google Maps data to standard merchant record."""
        try:
            name = raw_data.get("name", "").strip()
            if not name:
                return None

            return {
                "google_id": self._extract_google_id(raw_data),
                "name": name,
                "address": raw_data.get("address", ""),
                "lat": self._extract_lat(raw_data),
                "lng": self._extract_lng(raw_data),
                "rating": self._extract_rating(raw_data),
                "review_count": self._extract_review_count(raw_data),
                "phone": raw_data.get("phone", ""),
                "website": raw_data.get("website", ""),
                "hours": raw_data.get("hours", ""),
                "google_category": raw_data.get("google_category", ""),
                "status": raw_data.get("status", ""),
                "verified_badge": raw_data.get("verified_badge", ""),
                "our_category": category["name"],
                "vertical": category["vertical"],
                "kecamatan_name": district.kecamatan,
                "kabupaten_name": district.kabupaten,
                "provinsi_name": district.provinsi,
                "district_id": district.district_id,
            }
        except Exception as e:
            logger.error(f"Error parsing merchant: {e}")
            return None

    def _extract_google_id(self, data: dict) -> str:
        """Extract or generate a unique Google Maps ID."""
        if "google_id" in data:
            return data["google_id"]
        name = data.get("name", "unknown")
        address = data.get("address", "unknown")
        return f"gmaps_{hash((name, address)) % 10**10}"

    def _extract_lat(self, data: dict) -> Optional[float]:
        """Extract latitude coordinate."""
        try:
            lat = data.get("lat")
            if lat:
                return float(lat)
        except (ValueError, TypeError):
            pass
        return None

    def _extract_lng(self, data: dict) -> Optional[float]:
        """Extract longitude coordinate."""
        try:
            lng = data.get("lng")
            if lng:
                return float(lng)
        except (ValueError, TypeError):
            pass
        return None

    def _extract_rating(self, data: dict) -> Optional[float]:
        """Extract rating as float."""
        try:
            rating = data.get("rating")
            if rating:
                return float(rating)
        except (ValueError, TypeError):
            pass
        return None

    def _extract_review_count(self, data: dict) -> Optional[int]:
        """Extract review count as integer."""
        try:
            count = data.get("review_count")
            if count:
                if isinstance(count, str):
                    match = re.search(r"(\d+)", count)
                    if match:
                        return int(match.group(1))
                else:
                    return int(count)
        except (ValueError, TypeError):
            pass
        return None

