import random

# Google Maps Scraper Configuration
REQUEST_DELAY_MIN = 0.5  # seconds
REQUEST_DELAY_MAX = 3.0  # seconds
HEADLESS = True  # Run browser in headless mode
BROWSER_TIMEOUT = 30000  # milliseconds

OUTPUT_FIELDS = [
    "google_id", "name", "address", "lat", "lng",
    "rating", "review_count", "phone", "website", "hours",
    "google_category", "status", "verified_badge",
    "our_category", "vertical",
    "kecamatan_name", "kabupaten_name", "provinsi_name",
    "district_id",
    "scraped_at",
]

def get_random_delay():
    return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

CATEGORIES = [
    # --- FMCG (Field-sales friendly) ---
    {"id": 1, "name": "toko_kelontong", "vertical": "FMCG", "gmaps_query": "toko kelontong"},
    {"id": 2, "name": "laundry", "vertical": "FMCG", "gmaps_query": "laundry"},
    {"id": 3, "name": "pasar", "vertical": "FMCG", "gmaps_query": "pasar"},
    {"id": 4, "name": "toko_bahan_makanan", "vertical": "FMCG", "gmaps_query": "toko bahan makanan"},
    {"id": 5, "name": "stationery", "vertical": "FMCG", "gmaps_query": "stationery"},
    {"id": 6, "name": "home_goods", "vertical": "FMCG", "gmaps_query": "home goods"},
    {"id": 7, "name": "vapestore", "vertical": "FMCG", "gmaps_query": "vape store"},
    {"id": 8, "name": "toko_sepatu", "vertical": "FMCG", "gmaps_query": "toko sepatu"},
    {"id": 9, "name": "toko_pakaian", "vertical": "FMCG", "gmaps_query": "toko pakaian"},
    {"id": 10, "name": "toko_hp", "vertical": "FMCG", "gmaps_query": "toko hp"},
    {"id": 22, "name": "apotek", "vertical": "FMCG", "gmaps_query": "apotek"},
    {"id": 23, "name": "agen_pulsa", "vertical": "FMCG", "gmaps_query": "agen pulsa"},
    {"id": 24, "name": "toko_oleh_oleh", "vertical": "FMCG", "gmaps_query": "toko oleh oleh"},
    {"id": 25, "name": "toko_optik", "vertical": "FMCG", "gmaps_query": "toko optik"},
    {"id": 26, "name": "barbershop", "vertical": "FMCG", "gmaps_query": "barbershop"},

    # --- F&B (Field-sales friendly) ---
    {"id": 11, "name": "restaurant", "vertical": "F&B", "gmaps_query": "restaurant"},
    {"id": 12, "name": "cafe", "vertical": "F&B", "gmaps_query": "cafe"},
    {"id": 13, "name": "bakery", "vertical": "F&B", "gmaps_query": "bakery"},
    {"id": 14, "name": "warung_makan", "vertical": "F&B", "gmaps_query": "warung makan"},
    {"id": 15, "name": "warteg", "vertical": "F&B", "gmaps_query": "warteg"},
    {"id": 16, "name": "warung_padang", "vertical": "F&B", "gmaps_query": "warung padang"},
    {"id": 17, "name": "makanan_ringan", "vertical": "F&B", "gmaps_query": "makanan ringan"},
    {"id": 18, "name": "cake_shop", "vertical": "F&B", "gmaps_query": "cake shop"},
    {"id": 19, "name": "light_meal", "vertical": "F&B", "gmaps_query": "light meal"},
    {"id": 20, "name": "warung_ayam_goreng", "vertical": "F&B", "gmaps_query": "warung ayam goreng"},
    {"id": 21, "name": "rumah_mie", "vertical": "F&B", "gmaps_query": "rumah mie"},
    {"id": 27, "name": "warung_boba", "vertical": "F&B", "gmaps_query": "warung boba"},
    {"id": 28, "name": "juice_bar", "vertical": "F&B", "gmaps_query": "juice bar"},
    {"id": 29, "name": "nasi_kuning", "vertical": "F&B", "gmaps_query": "nasi kuning"},
    {"id": 30, "name": "tahu_goreng", "vertical": "F&B", "gmaps_query": "tahu goreng"},
]

CATEGORY_MAP = {c["name"]: c for c in CATEGORIES}
FMCG_CATEGORIES = [c["name"] for c in CATEGORIES if c["vertical"] == "FMCG"]
FNB_CATEGORIES = [c["name"] for c in CATEGORIES if c["vertical"] == "F&B"]
ALL_CATEGORY_NAMES = [c["name"] for c in CATEGORIES]
