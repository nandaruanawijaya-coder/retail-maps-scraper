"""Shared test fixtures for parser tests.

Contains real DOM text samples captured from Google Maps search results.
"""

import pytest


# Real contaminated address samples from 3172004 (Kota Depok) district
ADDRESS_SAMPLES = [
    ("Jl. Sungai Musi No.261A, RT.5/RW.1Buka", "Jl. Sungai Musi No.261A, RT.5/RW.1"),
    ("Jl. Swadaya II No.pos 03, RT.9/RW.011Buka 24 jam", "Jl. Swadaya II No.pos 03, RT.9/RW.011"),
    ("VW7Q+9QF, Kp. Sepatan, RT.18/RW.5Buka", "VW7Q+9QF, Kp. Sepatan, RT.18/RW.5"),
    ("Jl. Kebantenan V No.07, RT.6/RW.6Buka", "Jl. Kebantenan V No.07, RT.6/RW.6"),
    ("Jl. Merdeka No.12Tutup permanen", "Jl. Merdeka No.12"),
    ("Jl. Cilincing RT.5/RW.3Tutup sementara", "Jl. Cilincing RT.5/RW.3"),
    ("Jl. Pasar No.4Tutup pukul 20.00", "Jl. Pasar No.4"),
    ("Jl. Kelapa No.8Buka pukul 08.00", "Jl. Kelapa No.8"),
]

# Hours/status samples
HOURS_SAMPLES = [
    ("Jl. Maju No.5Buka", {"hours": "Buka", "status": "open"}),
    ("Jl. Maju No.5Buka 24 jam", {"hours": "Buka 24 jam", "status": "open"}),
    ("Jl. Maju No.5Tutup permanen", {"hours": "Tutup permanen", "status": "closed"}),
    ("Jl. Maju No.5", {"hours": None, "status": None}),
]

# Google category samples (from parts[0] of · split)
CATEGORY_SAMPLES = [
    ("Toko Berkah\nToko kelontong\n", "Toko kelontong"),
    ("Warung ABC\nRestoran\n", "Restoran"),
    ("Apotek Maju\nApotek\n", "Apotek"),
    ("Just a Store\n4.9\n", None),  # Rating, not category
]

# Review count samples
REVIEW_COUNT_SAMPLES = [
    ("(45)", 45),
    ("(1,234)", 1234),
    ("(1.234)", 1234),
    ("1.2k", 1200),
    ("1K", 1000),
    ("123 reviews", 123),
    ("1 review", 1),
    ("1.2kelauan", None),  # Kelauan bug test
    ("no reviews", None),
]

# Rating samples
RATING_SAMPLES = [
    ("4,9", 4.9),
    ("4.9", 4.9),
    ("5,0", 5.0),
    ("3.5", 3.5),
    ("(4.0)", 4.0),
    ("Rating: 4.5", 4.5),
    ("RT.5/RW.1", None),  # Address false positive
    ("No.12", None),  # Street number false positive
]

# Phone samples
PHONE_SAMPLES = [
    ("0819-2888-3661", "0819-2888-3661"),
    ("0812 3456 7890", "0812 3456 7890"),
    ("(021) 123-4567", "(021) 123-4567"),
    ("021-1234-5678", "021-1234-5678"),
    ("+62 812-3456-7890", "+62 812-3456-7890"),
    ("Telp. 021-123456", "021-123456"),
    ("WA: 081234567890", "081234567890"),
]

# Coordinate samples
COORD_SAMPLES = [
    (
        "/maps/place/Test/@-6.13,106.92,17z/data=!4m5!3m4!1s0x0!8m2!3d-6.1384297!4d106.921937",
        (-6.1384297, 106.921937),
    ),
    (
        "https://www.google.com/maps/place/Warung/@-6.1097075,106.9274033,17z",
        (-6.1097075, 106.9274033),
    ),
    ("!8m2!3d-8.670123!4d120.421456", (-8.670123, 120.421456)),
    ("@-8.670123,120.421456,15z", (-8.670123, 120.421456)),
    ("/maps/place/Test/data=!3m1!4b1", (None, None)),  # No coords
]


@pytest.fixture
def address_contaminated_samples():
    """Return pairs of (contaminated, expected_clean)."""
    return ADDRESS_SAMPLES


@pytest.fixture
def hours_status_samples():
    """Return pairs of (text, expected_dict)."""
    return HOURS_SAMPLES


@pytest.fixture
def category_samples():
    """Return pairs of (segment_zero, expected_category)."""
    return CATEGORY_SAMPLES


@pytest.fixture
def review_count_samples():
    """Return pairs of (text, expected_count)."""
    return REVIEW_COUNT_SAMPLES


@pytest.fixture
def rating_samples():
    """Return pairs of (text, expected_rating)."""
    return RATING_SAMPLES


@pytest.fixture
def phone_samples():
    """Return pairs of (text, expected_phone)."""
    return PHONE_SAMPLES


@pytest.fixture
def coord_samples():
    """Return pairs of (href, expected_tuple)."""
    return COORD_SAMPLES
