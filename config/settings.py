"""
Configuration settings.
Add Foursquare API key.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Existing settings
SERPAPI_KEY = os.getenv('SERPAPI_KEY')
SERPAPI_BASE_URL = "https://serpapi.com"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = "gpt-4o-mini"  # Using GPT-4o-mini model
REQUEST_DELAY = 0.5

# NEW: Foursquare API key
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')

# Business search queries
BUSINESS_SEARCH_QUERIES = {
    "cafe": "cafe coffee shop",
    "restaurant": "restaurant dining",
    "sneaker store": "sneaker store shoe shop",
    "pharmacy": "pharmacy medical store",
    "grocery": "grocery supermarket",
    "grocery shop": "grocery supermarket",
    "clothing store": "clothing fashion store",
    "electronics store": "electronics store",
    "bookstore": "bookstore",
    "bakery": "bakery",
    "barbershop": "barbershop hair salon",
    "gym": "gym fitness center",
    "bank": "bank financial services",
    "hotel": "hotel lodging",
    "jewellery shop": "jewellery jewelry store",
    "jewelry store": "jewellery jewelry store"
}

# NEW: Amenity search queries for enhanced insights
# Note: pharmacy has been intentionally excluded per project requirements
# Police, fire_station, and transit have been removed per user request
AMENITY_SEARCH_QUERIES = {
    "hospital": "hospitals medical centers",
    "clinic": "clinics healthcare centers",
    "school": "schools primary secondary",
    "university": "universities colleges higher education",
    "library": "public libraries",
    "park": "parks recreation areas"
}

# Default search radius for amenities (in meters)
AMENITY_SEARCH_RADIUS = 5000  # 5km

# Default demographics (fallback)
DEFAULT_DEMOGRAPHICS = {
    "population": 100000,
    "working_population": 60000,
    "income_level": 10000,
    "retail_shops": 200,
    "foot_traffic": 5000
}