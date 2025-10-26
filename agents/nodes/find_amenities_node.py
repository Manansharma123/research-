"""Find amenities node for business advisor workflow."""

import logging
from typing import Dict, Any, List
from agents.state import BusinessAnalysisState
from utils.api_clients import SerpApiClient
from utils.database import store_nearby_places, get_nearby_places
from config.settings import AMENITY_SEARCH_QUERIES as CONFIG_AMENITY_QUERIES

logger = logging.getLogger(__name__)

# Use amenity search queries from configuration
# Filter out pharmacy as it's been intentionally excluded
AMENITY_SEARCH_QUERIES = {
    k: v for k, v in CONFIG_AMENITY_QUERIES.items() 
    if k != "pharmacy"
}

def find_amenities_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to discover nearby amenities (hospitals, schools, universities).
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Updated state with nearby amenities information
    """
    logger.info("Starting find amenities node")
    
    try:
        latitude = state["latitude"]
        longitude = state["longitude"]
        # Use amenity types from filtered configuration
        # Remove police, fire_station, and transit as per user request
        amenity_types = [k for k in AMENITY_SEARCH_QUERIES.keys() if k not in ["police", "fire_station", "transit"]]
        
        # Dictionary to store all amenities by type
        all_amenities = {}
        
        for amenity_type in amenity_types:
            logger.info(f"Searching for nearby {amenity_type}s")
            
            try:
                # Fetch from API (no caching)
                search_query = AMENITY_SEARCH_QUERIES.get(amenity_type, f"{amenity_type}s near me")
                serp_client = SerpApiClient()
                
                search_results = serp_client.search_places(
                    query=search_query,
                    latitude=latitude,
                    longitude=longitude,
                    radius=5000  # 5km radius for amenities
                )
                
                # Parse results
                amenities = []
                if isinstance(search_results, dict) and "local_results" in search_results:
                    local_results = search_results["local_results"]
                    
                    for place in local_results[:10]:  # Limit to top 10
                        if not isinstance(place, dict):
                            continue
                        
                        # Extract position data correctly
                        position = place.get("gps_coordinates", {}) if "gps_coordinates" in place else place.get("position", {})
                        if not isinstance(position, dict):
                            position = {}
                        
                        # Add type checking for all values
                        name = place.get("title", "Unknown") if isinstance(place.get("title"), (str, type(None))) else "Unknown"
                        address = place.get("address", "No address") if isinstance(place.get("address"), (str, type(None))) else "No address"
                        rating = place.get("rating", 0) if isinstance(place.get("rating"), (int, float, type(None))) else 0
                        reviews_count = place.get("reviews", 0) if isinstance(place.get("reviews"), (int, float, type(None))) else 0
                        data_id = place.get("data_id", "") if isinstance(place.get("data_id"), (str, type(None))) else ""
                        
                        lat = position.get("latitude", latitude) if isinstance(position, dict) and isinstance(position.get("latitude"), (int, float)) else latitude
                        lon = position.get("longitude", longitude) if isinstance(position, dict) and isinstance(position.get("longitude"), (int, float)) else longitude
                        
                        amenity_info = {
                            "name": name,
                            "address": address,
                            "rating": rating,
                            "reviews_count": reviews_count,
                            "type": amenity_type,
                            "data_id": data_id,
                            "latitude": lat,
                            "longitude": lon,
                            "distance": _calculate_distance(
                                latitude, longitude,
                                lat,
                                lon
                            )
                        }
                        amenities.append(amenity_info)
                    
                    # Sort by distance
                    amenities.sort(key=lambda x: x.get("distance", float('inf')))
                    
                    # Store in database
                    if amenities:
                        store_nearby_places(amenities, latitude, longitude)
                    
                    all_amenities[amenity_type] = amenities
                    logger.info(f"Found {len(amenities)} {amenity_type}s")
            except Exception as amenity_error:
                logger.error(f"Error processing {amenity_type}: {str(amenity_error)}")
                all_amenities[amenity_type] = []
        
        return {
            **state,
            "nearby_amenities": all_amenities,
            "current_step": "find_amenities_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in find amenities node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "nearby_amenities": {},
            "error": error_msg,
            "current_step": "find_amenities_error"
        }

def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c