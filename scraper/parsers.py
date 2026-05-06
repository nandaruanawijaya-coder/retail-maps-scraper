"""Pure parsing functions for Google Maps merchant data extraction.

Each function takes raw text/href and returns cleaned, structured data.
No side effects, no DOM navigation — testable in isolation.
"""

import re
from typing import Optional, Tuple, Dict


# Regex to match Buka/Tutup status and everything after (service options, icons, etc)
# Uses negative lookbehind/lookahead to avoid matching place names like "Bukaka"
_STATUS_SUFFIX_RE = re.compile(
    r'(?<![A-Za-z])(Buka|Tutup)(?![A-Za-z]).*$',
    re.IGNORECASE | re.DOTALL
)


def parse_address(text: str) -> Optional[str]:
    """Strip open/closed status contamination from address text.

    Removes "Buka", "Tutup" and all text following them (service options, icons).
    Avoids matching place names that contain "Buka" (e.g., "Bukaka").
    Returns None if text is empty, whitespace-only, or only contains status.

    Args:
        text: Raw address segment (may contain "Buka"/"Tutup" suffix)

    Returns:
        Cleaned address string, or None if invalid.
    """
    if not text or not text.strip():
        return None

    stripped = text.strip()

    # Strip Buka/Tutup and everything following (service options, icons, quotes)
    cleaned = _STATUS_SUFFIX_RE.sub('', stripped).strip()

    # Return None if nothing meaningful remains (e.g., input was "Buka sekarang")
    if not cleaned or len(cleaned) < 3:
        return None

    return cleaned


def parse_hours_status(text: str) -> Dict:
    """Extract the open/closed status phrase from contaminated text.

    Args:
        text: Raw text that may contain "Buka" or "Tutup"

    Returns:
        {"hours": str or None, "status": "open"|"closed"|None}
    """
    null_result = {"hours": None, "status": None}
    if not text or not text.strip():
        return null_result

    m = re.search(
        r'(?<![A-Za-z])(Buka|Tutup)(?![A-Za-z]).*?(?=\s{2,}|\xa0|$)',
        text,
        re.IGNORECASE
    )

    if not m:
        return null_result

    hours = m.group(0).strip()
    status = "open" if m.group(1).lower().startswith("buka") else "closed"
    return {"hours": hours, "status": status}


def parse_google_category(segment_zero: str) -> Optional[str]:
    """Extract Google Maps category label from merchant segment.

    Category appears after rating (e.g. "Tip Top Depok 4,5Supermarket Diskon")
    or as a separate line. Handles both formats.

    Args:
        segment_zero: First segment from text.split('·') (name + rating + category)

    Returns:
        Category label string, or None if not found.
    """
    if not segment_zero or not segment_zero.strip():
        return None

    text = segment_zero.strip()

    m = re.search(r'[4-5][,\.][0-9](?:\s*\(\d+\))?\s*([A-Za-z][A-Za-z\s]*?)$', text)
    if m:
        category = m.group(1).strip()
        if 2 <= len(category) <= 80 and not re.match(r'^\d', category):
            return category

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) >= 2:
        for category_candidate in reversed(lines):
            if re.match(r'^\(?\d', category_candidate):
                continue
            if len(category_candidate) < 2 or len(category_candidate) > 80:
                continue
            if len(lines) >= 2 and category_candidate == lines[0]:
                continue
            return category_candidate

    return None


def parse_rating(text: Optional[str]) -> Optional[float]:
    """Extract merchant rating avoiding false positives.

    Avoids matching RT.5/RW.1 address notation or street numbers.
    Only returns valid 1.0–5.0 range.

    Args:
        text: Any text that may contain a rating

    Returns:
        Float rating 1.0–5.0, or None if not found.
    """
    if not text or not text.strip():
        return None

    m = re.search(r'(?<![/\w])([1-5][,\.][0-9])(?!\d)', str(text))
    if m:
        try:
            rating = float(m.group(1).replace(',', '.'))
            if 1.0 <= rating <= 5.0:
                return rating
        except ValueError:
            pass

    return None


def parse_review_count(text: Optional[str]) -> Optional[int]:
    """Extract review count with kelauan bug fix.

    Handles: (123), (1,234), (1.234), 1.2k, 1K, "123 reviews"

    Args:
        text: Any text that may contain a review count

    Returns:
        Integer review count, or None if not found.
    """
    if not text:
        return None

    text_lower = str(text).strip().lower()
    if not text_lower:
        return None

    m = re.search(r'\((\d+(?:[,.]\d+)*)\)', text_lower)
    if m:
        num_str = re.sub(r'[,.]', '', m.group(1))
        if num_str.isdigit():
            return int(num_str)

    m = re.search(r'(\d+(?:[,.\s]\d+)*)\s*reviews?(?!\w)', text_lower)
    if m:
        num_str = re.sub(r'[,.\s]', '', m.group(1))
        if num_str.isdigit():
            return int(num_str)

    m = re.search(r'(\d+(?:[,.]\d+)?)\s*k\b(?!elauan)', text_lower)
    if m:
        num_str = m.group(1).replace(',', '.').replace(' ', '')
        try:
            return int(float(num_str) * 1000)
        except ValueError:
            pass

    return None


def parse_phone(text: Optional[str]) -> Optional[str]:
    """Extract Indonesian phone number supporting multiple formats.

    Handles: 0812-3456-7890, 0812 3456 7890, (021) 123-4567,
             +6221-1234567, 081234567890, with optional prefixes.

    Args:
        text: Any text that may contain a phone number

    Returns:
        First matched phone number string, or None.
    """
    if not text or not str(text).strip():
        return None

    phone_re = re.compile(
        r'(\+62[\s-]?\d[\d\s-]{7,13}'
        r'|\(\d{3,4}\)[\s-]?\d{3,5}[\s-]?\d{3,5}'
        r'|0\d{2,3}[\s-]\d{3,4}[\s-]\d{3,4}'
        r'|0\d{2,3}[\s-]\d{6}'
        r'|0\d{9,12})',
    )

    m = phone_re.search(str(text))
    if m:
        return m.group(0).strip()

    return None


def parse_coords_from_href(href: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from Google Maps place href.

    Tries two patterns in order:
    1. !8m2!3d[lat]!4d[lng] (preferred, more precise)
    2. @[lat],[lng] (fallback, less precise)

    Args:
        href: The href attribute from <a href="/maps/place/...">

    Returns:
        Tuple of (lat, lng) as floats, or (None, None) if not found.
    """
    if not href or not href.strip():
        return None, None

    m = re.search(r'!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', href)
    if m:
        return float(m.group(1)), float(m.group(2))

    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
    if m:
        return float(m.group(1)), float(m.group(2))

    return None, None


def parse_website(text: Optional[str]) -> Optional[str]:
    """Extract website URL from merchant text.

    Looks for URL patterns (http/https, www, or domain.tld).
    Avoids extracting coordinates or other false positives.

    Args:
        text: Any text that may contain a website URL

    Returns:
        First matched URL string, or None if not found.
    """
    if not text or not str(text).strip():
        return None

    url_re = re.compile(
        r'(?:https?://)?(?:www\.)?'
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
        r'(?:\.[a-zA-Z]{2,}){1,3}'
        r'(?:/[^\s]*)?'
    )

    m = url_re.search(str(text))
    if m:
        url = m.group(0).strip()
        if len(url) > 6 and not re.match(r'^\d+\.\d+', url):
            return url

    return None


def parse_verified_badge(text: Optional[str]) -> Optional[bool]:
    """Detect if merchant has verified badge in Google Maps.

    Looks for indicators like checkmark, "verified", "official", etc.

    Args:
        text: Any text that may contain verification indicators

    Returns:
        True if verified badge detected, False if explicitly marked unverified, None if unknown.
    """
    if not text:
        return None

    text_lower = str(text).lower().strip()

    verified_indicators = [
        r'✓',
        r'verified',
        r'official',
        r'google verified',
        r'officially verified',
    ]

    for pattern in verified_indicators:
        if re.search(pattern, text_lower):
            return True

    return None
