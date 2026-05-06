"""Unit tests for scraper.parsers module using TDD RED-GREEN-REFACTOR.

Each test class focuses on one parser function.
Fixtures from conftest.py provide real DOM samples.
"""

import pytest
from scraper.parsers import (
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


class TestParseAddress:
    """Tests for address contamination stripping - Task 1."""

    # === CORE CONTAMINATION PATTERNS (from real data) ===

    def test_strips_bare_buka(self):
        """Strip 'Buka' suffix from address."""
        result = parse_address("Jl. Sungai Musi No.261A, RT.5/RW.1Buka")
        assert result == "Jl. Sungai Musi No.261A, RT.5/RW.1"

    def test_strips_buka_24_jam(self):
        """Strip 'Buka 24 jam' suffix."""
        result = parse_address("Jl. Swadaya II No.pos 03, RT.9/RW.011Buka 24 jam")
        assert result == "Jl. Swadaya II No.pos 03, RT.9/RW.011"

    def test_strips_buka_sekarang(self):
        """Strip 'Buka sekarang' suffix."""
        result = parse_address("Jl. Kebantenan No.5Buka sekarang")
        assert result == "Jl. Kebantenan No.5"

    def test_strips_buka_sekarang_with_service_options(self):
        """Strip 'Buka sekarang' with trailing service options (\xa0 separator)."""
        result = parse_address("Jl. Maju No.7Buka sekarang\xa0 Makan di tempat")
        assert result == "Jl. Maju No.7"

    def test_strips_buka_24_jam_with_service_options(self):
        """Strip 'Buka 24 jam' with trailing service options."""
        result = parse_address("Jl. Raya No.3Buka 24 jam\xa0 Pesan antar")
        assert result == "Jl. Raya No.3"

    def test_strips_bare_tutup(self):
        """Strip 'Tutup' suffix."""
        result = parse_address("Jl. Cilincing RT.5/RW.3Tutup")
        assert result == "Jl. Cilincing RT.5/RW.3"

    def test_strips_tutup_permanen(self):
        """Strip 'Tutup permanen' suffix."""
        result = parse_address("Jl. Kali Baru No.12Tutup permanen")
        assert result == "Jl. Kali Baru No.12"

    def test_strips_tutup_sementara(self):
        """Strip 'Tutup sementara' suffix."""
        result = parse_address("Jl. Merdeka No.1Tutup sementara")
        assert result == "Jl. Merdeka No.1"

    def test_strips_tutup_pukul(self):
        """Strip 'Tutup pukul HH.mm' suffix."""
        result = parse_address("Jl. Pasar No.4Tutup pukul 20.00")
        assert result == "Jl. Pasar No.4"

    def test_strips_buka_pukul(self):
        """Strip 'Buka pukul HH.mm' suffix."""
        result = parse_address("Jl. Kelapa No.8Buka pukul 08.00")
        assert result == "Jl. Kelapa No.8"

    def test_plus_code_with_buka(self):
        """Strip 'Buka' from Plus Code address."""
        result = parse_address("VW7Q+9QF, Kp. Sepatan, RT.18/RW.5Buka")
        assert result == "VW7Q+9QF, Kp. Sepatan, RT.18/RW.5"

    def test_plus_code_complex_with_buka(self):
        """Strip 'Buka' from complex Plus Code with kelurahan."""
        result = parse_address("FV35+389, Kelurahan Baru, RT.5/RW.2Buka")
        assert result == "FV35+389, Kelurahan Baru, RT.5/RW.2"

    # === CLEAN INPUTS — must NOT modify ===

    def test_clean_address_unchanged(self):
        """Clean address without status suffix unchanged."""
        result = parse_address("Jl. Sudirman No.5, RT.3/RW.1")
        assert result == "Jl. Sudirman No.5, RT.3/RW.1"

    def test_address_with_kelurahan_no_contamination(self):
        """Place names starting with 'Buka' not stripped (e.g., Bukaka village)."""
        result = parse_address("Jl. Maju Raya, Kelurahan Bukaka")
        assert result == "Jl. Maju Raya, Kelurahan Bukaka"

    # === EDGE CASES ===

    def test_returns_none_for_status_only(self):
        """Text with only status (no address) returns None."""
        result = parse_address("Buka sekarang")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_address("")
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only string returns None."""
        result = parse_address("   ")
        assert result is None

    def test_strips_unicode_icons_after_buka(self):
        """Unicode icons after 'Buka' are stripped."""
        result = parse_address("Jl. Test No.1Buka sekarang")
        assert result == "Jl. Test No.1"


class TestParseHoursStatus:
    """Tests for hours/status extraction - Task 2."""

    # === CORE EXTRACTION PATTERNS ===

    def test_extracts_bare_buka(self):
        """Extract 'Buka' status with open state."""
        result = parse_hours_status("Jl. Maju No.5Buka")
        assert result == {"hours": "Buka", "status": "open"}

    def test_extracts_buka_24_jam(self):
        """Extract 'Buka 24 jam' with open state."""
        result = parse_hours_status("Jl. Maju No.5Buka 24 jam")
        assert result == {"hours": "Buka 24 jam", "status": "open"}

    def test_extracts_buka_sekarang(self):
        """Extract 'Buka sekarang' with open state."""
        result = parse_hours_status("Jl. Maju No.5Buka sekarang")
        assert result == {"hours": "Buka sekarang", "status": "open"}

    def test_extracts_buka_pukul(self):
        """Extract 'Buka pukul HH.mm' with open state."""
        result = parse_hours_status("Jl. Kelapa No.8Buka pukul 08.00")
        assert result == {"hours": "Buka pukul 08.00", "status": "open"}

    def test_extracts_bare_tutup(self):
        """Extract 'Tutup' status with closed state."""
        result = parse_hours_status("Jl. Cilincing RT.5/RW.3Tutup")
        assert result == {"hours": "Tutup", "status": "closed"}

    def test_extracts_tutup_permanen(self):
        """Extract 'Tutup permanen' with closed state."""
        result = parse_hours_status("Jl. Merdeka No.1Tutup permanen")
        assert result == {"hours": "Tutup permanen", "status": "closed"}

    def test_extracts_tutup_sementara(self):
        """Extract 'Tutup sementara' with closed state."""
        result = parse_hours_status("Jl. Merdeka No.12Tutup sementara")
        assert result == {"hours": "Tutup sementara", "status": "closed"}

    def test_extracts_tutup_pukul(self):
        """Extract 'Tutup pukul HH.mm' with closed state."""
        result = parse_hours_status("Jl. Pasar No.4Tutup pukul 20.00")
        assert result == {"hours": "Tutup pukul 20.00", "status": "closed"}

    # === SERVICE OPTIONS HANDLING ===

    def test_stops_at_service_options_nbsp(self):
        """Stop extracting hours at non-breaking space (service options marker)."""
        result = parse_hours_status("Jl. Maju No.7Buka sekarang\xa0 Makan di tempat")
        assert result == {"hours": "Buka sekarang", "status": "open"}

    def test_stops_at_service_options_double_space(self):
        """Stop extracting hours at double space (service options marker)."""
        result = parse_hours_status("Jl. Raya No.3Buka 24 jam  Pesan antar")
        assert result == {"hours": "Buka 24 jam", "status": "open"}

    # === EDGE CASES ===

    def test_returns_null_for_no_status(self):
        """Text with no status returns null result."""
        result = parse_hours_status("Jl. Maju No.5")
        assert result == {"hours": None, "status": None}

    def test_returns_null_for_empty_string(self):
        """Empty string returns null result."""
        result = parse_hours_status("")
        assert result == {"hours": None, "status": None}

    def test_returns_null_for_whitespace_only(self):
        """Whitespace-only string returns null result."""
        result = parse_hours_status("   ")
        assert result == {"hours": None, "status": None}


class TestParseGoogleCategory:
    """Tests for Google Maps category extraction - Task 3."""

    # === CORE EXTRACTION PATTERNS ===

    def test_extracts_retail_category(self):
        """Extract category from retail store format (name + category)."""
        result = parse_google_category("Toko Berkah\nToko kelontong\n")
        assert result == "Toko kelontong"

    def test_extracts_restaurant_category(self):
        """Extract category from restaurant format."""
        result = parse_google_category("Warung ABC\nRestoran\n")
        assert result == "Restoran"

    def test_extracts_pharmacy_category(self):
        """Extract category from pharmacy format."""
        result = parse_google_category("Apotek Maju\nApotek\n")
        assert result == "Apotek"

    def test_extracts_category_with_spaces(self):
        """Extract category with leading/trailing whitespace."""
        result = parse_google_category("Store Name\n   Grocery Store   \n")
        assert result == "Grocery Store"

    def test_extracts_multiword_category(self):
        """Extract category with multiple words."""
        result = parse_google_category("Toko\nToko Bahan Makanan\n")
        assert result == "Toko Bahan Makanan"

    # === REJECTION PATTERNS ===

    def test_rejects_rating_as_category(self):
        """Reject if second line looks like a rating (starts with digit)."""
        result = parse_google_category("Just a Store\n4.9\n")
        assert result is None

    def test_rejects_numeric_only_line(self):
        """Reject if category candidate is numeric."""
        result = parse_google_category("Store\n123\n")
        assert result is None

    # === EDGE CASES ===

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_google_category("")
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only string returns None."""
        result = parse_google_category("   ")
        assert result is None

    def test_returns_none_for_single_line(self):
        """Single line (no category line) returns None."""
        result = parse_google_category("Store Name\n")
        assert result is None

    def test_returns_none_for_too_short_category(self):
        """Category too short (< 2 chars) returns None."""
        result = parse_google_category("Store\nA\n")
        assert result is None


class TestParseReviewCount:
    """Tests for review count extraction with kelauan bug fix - Task 4."""

    # === PARENTHESES FORMAT ===

    def test_extracts_simple_count_in_parens(self):
        """Extract simple count in parentheses."""
        result = parse_review_count("(45)")
        assert result == 45

    def test_extracts_count_with_comma_separator(self):
        """Extract count with comma separator (1,234)."""
        result = parse_review_count("(1,234)")
        assert result == 1234

    def test_extracts_count_with_period_separator(self):
        """Extract count with period separator (1.234) - European format."""
        result = parse_review_count("(1.234)")
        assert result == 1234

    # === TEXT FORMAT ===

    def test_extracts_count_with_reviews_suffix(self):
        """Extract count from 'N reviews' text."""
        result = parse_review_count("123 reviews")
        assert result == 123

    def test_extracts_count_from_singular_review(self):
        """Extract count from '1 review' text."""
        result = parse_review_count("1 review")
        assert result == 1

    def test_extracts_count_with_comma_in_text_format(self):
        """Extract count with comma in 'N,NNN reviews' format."""
        result = parse_review_count("2,345 reviews")
        assert result == 2345

    # === THOUSANDS FORMAT ===

    def test_extracts_count_in_k_format(self):
        """Extract count in 'NK' format (1k = 1000)."""
        result = parse_review_count("1K")
        assert result == 1000

    def test_extracts_count_in_lowercase_k_format(self):
        """Extract count in lowercase 'Nk' format."""
        result = parse_review_count("1.2k")
        assert result == 1200

    def test_extracts_count_with_decimal_k(self):
        """Extract count in 'N.NK' format (1.5k = 1500)."""
        result = parse_review_count("2.5K")
        assert result == 2500

    # === KELAUAN BUG TESTS ===

    def test_rejects_kelauan_false_positive(self):
        """REGRESSION: Reject 'kelauan' (Indonesian word) as thousand marker."""
        result = parse_review_count("1.2kelauan")
        assert result is None

    def test_rejects_kelauan_in_text(self):
        """Reject 'kelauan' even in longer text."""
        result = parse_review_count("Text with 5.3kelauan here")
        assert result is None

    # === EDGE CASES ===

    def test_returns_none_for_no_match(self):
        """Non-matching text returns None."""
        result = parse_review_count("no reviews")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_review_count("")
        assert result is None

    def test_returns_none_for_none_input(self):
        """None input returns None."""
        result = parse_review_count(None)
        assert result is None


class TestParseRating:
    """Tests for rating extraction with false positive prevention - Task 5."""

    # === CORE FORMATS ===

    def test_extracts_rating_with_comma_separator(self):
        """Extract rating with comma separator (European format)."""
        result = parse_rating("4,9")
        assert result == 4.9

    def test_extracts_rating_with_period_separator(self):
        """Extract rating with period separator."""
        result = parse_rating("4.9")
        assert result == 4.9

    def test_extracts_rating_5_0(self):
        """Extract 5-star rating."""
        result = parse_rating("5,0")
        assert result == 5.0

    def test_extracts_rating_1_0(self):
        """Extract 1-star rating (minimum)."""
        result = parse_rating("1.0")
        assert result == 1.0

    def test_extracts_rating_in_parentheses(self):
        """Extract rating enclosed in parentheses."""
        result = parse_rating("(4.0)")
        assert result == 4.0

    def test_extracts_rating_with_label(self):
        """Extract rating from labeled text."""
        result = parse_rating("Rating: 4.5")
        assert result == 4.5

    def test_extracts_rating_in_sentence(self):
        """Extract rating from sentence."""
        result = parse_rating("This place has 3.7 stars")
        assert result == 3.7

    # === FALSE POSITIVE PREVENTION ===

    def test_rejects_address_notation_rt_rw(self):
        """Reject RT.5/RW.1 address notation (false positive)."""
        result = parse_rating("RT.5/RW.1")
        assert result is None

    def test_rejects_street_number_notation(self):
        """Reject No.12 street number notation."""
        result = parse_rating("No.12")
        assert result is None

    def test_rejects_rw_only_notation(self):
        """Reject RW.5 notation."""
        result = parse_rating("RW.5")
        assert result is None

    def test_rejects_rating_above_5(self):
        """Reject rating above 5.0 (out of range)."""
        result = parse_rating("6.5")
        assert result is None

    def test_rejects_rating_below_1(self):
        """Reject rating below 1.0 (out of range)."""
        result = parse_rating("0.9")
        assert result is None

    def test_rejects_rating_with_trailing_digits(self):
        """Reject if there are digits after the decimal digit."""
        result = parse_rating("4.95")
        assert result is None

    # === EDGE CASES ===

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_rating("")
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only string returns None."""
        result = parse_rating("   ")
        assert result is None

    def test_returns_none_for_no_match(self):
        """Non-matching text returns None."""
        result = parse_rating("No rating found")
        assert result is None

    def test_returns_none_for_none_input(self):
        """None input returns None."""
        result = parse_rating(None)
        assert result is None


class TestParsePhone:
    """Tests for Indonesian phone number extraction - Task 6."""

    # === MOBILE FORMAT: 0XXXXXXXXX ===

    def test_extracts_mobile_dashed_format(self):
        """Extract mobile number with dashes (0819-2888-3661)."""
        result = parse_phone("0819-2888-3661")
        assert result == "0819-2888-3661"

    def test_extracts_mobile_space_separated(self):
        """Extract mobile number with spaces (0812 3456 7890)."""
        result = parse_phone("0812 3456 7890")
        assert result == "0812 3456 7890"

    def test_extracts_mobile_continuous(self):
        """Extract mobile number without separators (081234567890)."""
        result = parse_phone("081234567890")
        assert result == "081234567890"

    # === AREA CODE FORMAT: (0XX) XXXX-XXXX ===

    def test_extracts_area_code_with_parentheses(self):
        """Extract area code format (021) 123-4567."""
        result = parse_phone("(021) 123-4567")
        assert result == "(021) 123-4567"

    def test_extracts_area_code_dashed(self):
        """Extract area code with dashes (021-1234-5678)."""
        result = parse_phone("021-1234-5678")
        assert result == "021-1234-5678"

    # === INTERNATIONAL FORMAT: +62 XXX-XXXX-XXXX ===

    def test_extracts_international_format(self):
        """Extract international format +62 812-3456-7890."""
        result = parse_phone("+62 812-3456-7890")
        assert result == "+62 812-3456-7890"

    def test_extracts_international_continuous(self):
        """Extract international format without separators (+62812345678)."""
        result = parse_phone("+62812345678")
        assert result == "+62812345678"

    # === EXTRACTION FROM TEXT ===

    def test_extracts_phone_with_telp_prefix(self):
        """Extract phone number with 'Telp.' prefix."""
        result = parse_phone("Telp. 021-123456")
        assert result == "021-123456"

    def test_extracts_phone_with_wa_prefix(self):
        """Extract phone number with 'WA:' prefix."""
        result = parse_phone("WA: 081234567890")
        assert result == "081234567890"

    def test_extracts_phone_from_sentence(self):
        """Extract phone number from sentence."""
        result = parse_phone("Call us at 0812-3456-7890 for more info")
        assert result == "0812-3456-7890"

    def test_extracts_first_phone_from_multiple(self):
        """Extract first phone when multiple present."""
        result = parse_phone("0812-1234-5678 or 0821-9876-5432")
        assert result == "0812-1234-5678"

    # === EDGE CASES ===

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_phone("")
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only string returns None."""
        result = parse_phone("   ")
        assert result is None

    def test_returns_none_for_no_match(self):
        """Non-matching text returns None."""
        result = parse_phone("No phone number here")
        assert result is None

    def test_returns_none_for_none_input(self):
        """None input returns None."""
        result = parse_phone(None)
        assert result is None


class TestParseCoordsFromHref:
    """Tests for coordinate extraction from Google Maps href - Task 7."""

    # === PATTERN 1: !8m2!3d[lat]!4d[lng] (Preferred, high precision) ===

    def test_extracts_coords_from_8m2_pattern(self):
        """Extract coordinates using !8m2! pattern (high precision)."""
        href = "/maps/place/Test/@-6.13,106.92,17z/data=!4m5!3m4!1s0x0!8m2!3d-6.1384297!4d106.921937"
        result = parse_coords_from_href(href)
        assert result == (-6.1384297, 106.921937)

    def test_extracts_8m2_pattern_standalone(self):
        """Extract coordinates from standalone !8m2! pattern."""
        href = "!8m2!3d-8.670123!4d120.421456"
        result = parse_coords_from_href(href)
        assert result == (-8.670123, 120.421456)

    def test_extracts_positive_coords_8m2_pattern(self):
        """Extract positive coordinates (northeast of equator/prime meridian)."""
        href = "!8m2!3d10.5!4d50.25"
        result = parse_coords_from_href(href)
        assert result == (10.5, 50.25)

    # === PATTERN 2: @[lat],[lng] (Fallback, lower precision) ===

    def test_extracts_coords_from_at_pattern(self):
        """Extract coordinates using @ pattern (lower precision)."""
        href = "https://www.google.com/maps/place/Warung/@-6.1097075,106.9274033,17z"
        result = parse_coords_from_href(href)
        assert result == (-6.1097075, 106.9274033)

    def test_extracts_at_pattern_standalone(self):
        """Extract coordinates from standalone @ pattern."""
        href = "@-8.670123,120.421456,15z"
        result = parse_coords_from_href(href)
        assert result == (-8.670123, 120.421456)

    def test_prefers_8m2_over_at_pattern(self):
        """If both patterns present, prefer !8m2! (more precise)."""
        href = "@-6.1,106.9,17z/data=!8m2!3d-6.1384297!4d106.921937"
        result = parse_coords_from_href(href)
        assert result == (-6.1384297, 106.921937)

    # === EDGE CASES ===

    def test_returns_none_for_no_coords(self):
        """Returns (None, None) when no coordinates found."""
        href = "/maps/place/Test/data=!3m1!4b1"
        result = parse_coords_from_href(href)
        assert result == (None, None)

    def test_returns_none_for_empty_string(self):
        """Empty string returns (None, None)."""
        result = parse_coords_from_href("")
        assert result == (None, None)

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only string returns (None, None)."""
        result = parse_coords_from_href("   ")
        assert result == (None, None)

    def test_returns_none_for_none_input(self):
        """None input returns (None, None)."""
        result = parse_coords_from_href(None)
        assert result == (None, None)

    def test_handles_scientific_notation(self):
        """Handle coordinates in decimal notation (normal format)."""
        href = "!8m2!3d-34.397!4d150.644"
        result = parse_coords_from_href(href)
        assert result == (-34.397, 150.644)


class TestParseWebsite:
    """Tests for website URL extraction."""

    # === HTTPS/HTTP URLs ===

    def test_extracts_https_url(self):
        """Extract HTTPS URL."""
        result = parse_website("Visit us at https://www.example.com for more info")
        assert result == "https://www.example.com"

    def test_extracts_http_url(self):
        """Extract HTTP URL."""
        result = parse_website("Our site: http://example.com")
        assert result == "http://example.com"

    # === WWW URLs ===

    def test_extracts_www_url(self):
        """Extract www.domain.tld format."""
        result = parse_website("Website: www.example.com")
        assert result == "www.example.com"

    def test_extracts_www_with_path(self):
        """Extract www.domain.tld with path."""
        result = parse_website("www.restaurant.co.id/menu")
        assert result == "www.restaurant.co.id/menu"

    # === DOMAIN-ONLY URLs ===

    def test_extracts_bare_domain(self):
        """Extract bare domain.tld format."""
        result = parse_website("example.com")
        assert result == "example.com"

    def test_extracts_domain_with_subdomain(self):
        """Extract subdomain.domain.tld format."""
        result = parse_website("Check out cafe.restaurant.co.id")
        assert result == "cafe.restaurant.co.id"

    def test_extracts_indonesian_tld(self):
        """Extract Indonesian .co.id domain."""
        result = parse_website("Kunjungi toko.co.id untuk info")
        assert result == "toko.co.id"

    # === FROM TEXT ===

    def test_extracts_url_from_sentence(self):
        """Extract URL from sentence."""
        result = parse_website("Call us or visit www.store.com today!")
        assert result == "www.store.com"

    def test_extracts_first_url_from_multiple(self):
        """Extract first URL when multiple present."""
        result = parse_website("Main: www.store.com or backup: example.com")
        assert result == "www.store.com"

    # === EDGE CASES ===

    def test_rejects_ip_address(self):
        """Reject IP addresses (too short)."""
        result = parse_website("192.168.1.1")
        assert result is None

    def test_rejects_coordinates_as_url(self):
        """Don't match coordinates as URLs."""
        result = parse_website("-6.1234,106.5678")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_website("")
        assert result is None

    def test_returns_none_for_no_url(self):
        """Text without URL returns None."""
        result = parse_website("No website here")
        assert result is None

    def test_returns_none_for_none_input(self):
        """None input returns None."""
        result = parse_website(None)
        assert result is None


class TestParseVerifiedBadge:
    """Tests for verified badge detection."""

    # === EXPLICIT INDICATORS ===

    def test_detects_verified_keyword(self):
        """Detect 'verified' keyword."""
        result = parse_verified_badge("✓ Verified by Google Maps")
        assert result is True

    def test_detects_official_keyword(self):
        """Detect 'official' keyword."""
        result = parse_verified_badge("Official restaurant account")
        assert result is True

    def test_detects_google_verified(self):
        """Detect 'Google verified' phrase."""
        result = parse_verified_badge("Google verified merchant")
        assert result is True

    def test_detects_checkmark_symbol(self):
        """Detect checkmark symbol."""
        result = parse_verified_badge("✓")
        assert result is True

    def test_detects_officially_verified(self):
        """Detect 'officially verified' phrase."""
        result = parse_verified_badge("Officially verified business")
        assert result is True

    # === CASE INSENSITIVITY ===

    def test_detects_uppercase_verified(self):
        """Detect uppercase VERIFIED."""
        result = parse_verified_badge("VERIFIED")
        assert result is True

    def test_detects_mixed_case(self):
        """Detect mixed case Verified."""
        result = parse_verified_badge("This account is Verified here")
        assert result is True

    # === CONTEXT ===

    def test_detects_in_sentence(self):
        """Detect verification indicator in sentence."""
        result = parse_verified_badge("This is an official merchant with verified badge")
        assert result is True

    # === NEGATIVE CASES ===

    def test_returns_none_for_unverified_text(self):
        """Text without verification indicators returns None."""
        result = parse_verified_badge("Regular merchant")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        result = parse_verified_badge("")
        assert result is None

    def test_returns_none_for_none_input(self):
        """None input returns None."""
        result = parse_verified_badge(None)
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only returns None."""
        result = parse_verified_badge("   ")
        assert result is None
