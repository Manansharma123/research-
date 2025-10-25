"""Simple scraper using Google Places API (no SERPAPI needed)."""

import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')


def search_businesses(business_type: str, location: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """
    Search for businesses using Google Places API (Text Search).
    
    Args:
        business_type: Type of business (e.g., 'cafe', 'restaurant')
        location: Location to search (e.g., 'The Zirk, Zirakpur')
        latitude: Optional latitude for location bias
        longitude: Optional longitude for location bias
        
    Returns:
        List of business data dictionaries
    """
    if not GOOGLE_PLACES_API_KEY:
        print("⚠️  GOOGLE_PLACES_API_KEY not found")
        return []
    
    # Build search query
    query = f"{business_type} in {location}"
    
    # Google Places Text Search endpoint
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': GOOGLE_PLACES_API_KEY,
    }
    
    # Add location bias if coordinates provided
    if latitude and longitude:
        params['location'] = f"{latitude},{longitude}"
        params['radius'] = 3000  # 3km radius
    
    try:
        print(f"🔍 Searching Google Places: {query}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            print(f"❌ API Error: {data.get('status')}")
            return []
        
        # Extract results
        results = data.get('results', [])
        
        if not results:
            print("❌ No results found")
            return []
        
        # Format results
        businesses = []
        for result in results[:15]:  # Limit to 15 results
            business = {
                'name': result.get('name', 'N/A'),
                'rating': result.get('rating', 'N/A'),
                'reviews': result.get('user_ratings_total', 0),
                'type': ', '.join(result.get('types', [])[:3]),
                'address': result.get('formatted_address', 'N/A'),
                'price_level': '₹' * result.get('price_level', 0) if result.get('price_level') else 'N/A',
                'business_status': result.get('business_status', 'N/A'),
            }
            businesses.append(business)
        
        print(f"✅ Found {len(businesses)} businesses")
        return businesses
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def search_schools(location: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """
    Search for schools using Google Places API.
    
    Args:
        location: Location to search
        latitude: Optional latitude
        longitude: Optional longitude
        
    Returns:
        List of school data dictionaries
    """
    return search_businesses("schools", location, latitude, longitude)
