"""Find businesses node for business advisor workflow."""

import logging
from typing import Dict, Any, List
from agents.state import BusinessAnalysisState
from utils.api_clients import SerpApiClient
from config.settings import BUSINESS_SEARCH_QUERIES
from utils.database import store_nearby_places, get_nearby_places

logger = logging.getLogger(__name__)


def find_businesses_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to discover nearby businesses of the specified type.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with nearby businesses information
    """
    logger.info("Starting find businesses node")
    
    try:
        # Extract information from state
        latitude = state["latitude"]
        longitude = state["longitude"]
        business_type = state["business_type"]
        
        # Get search query for business type (no caching)
        search_query = BUSINESS_SEARCH_QUERIES.get(business_type, business_type)
        logger.info(f"Searching for {business_type} businesses with query: {search_query}")
        
        # Initialize SerpApi client
        serp_client = SerpApiClient()
        
        # Search for nearby businesses
        search_results = serp_client.search_places(
            query=search_query,
            latitude=latitude,
            longitude=longitude,
            radius=3000  # 3km radius
        )
        
        # Debug: Log the search results structure
        logger.debug(f"Search results type: {type(search_results)}")
        logger.debug(f"Search results keys: {search_results.keys() if isinstance(search_results, dict) else 'Not a dict'}")
        
        # Extract business information
        nearby_businesses = []
        if isinstance(search_results, dict) and "local_results" in search_results:
            local_results = search_results["local_results"]
            logger.debug(f"Local results type: {type(local_results)}")
            logger.debug(f"Local results length: {len(local_results) if hasattr(local_results, '__len__') else 'No length'}")
            
            if isinstance(local_results, list):
                for business in local_results:
                    # Debug: Log business structure
                    logger.debug(f"Business type: {type(business)}")
                    logger.debug(f"Business keys: {business.keys() if isinstance(business, dict) else 'Not a dict'}")
                    
                    if not isinstance(business, dict):
                        logger.warning(f"Skipping non-dict business entry: {business}")
                        continue
                    
                    # Extract latitude and longitude from gps_coordinates if available
                    gps_coordinates = business.get("gps_coordinates", {})
                    position = business.get("position", {})
                    if isinstance(gps_coordinates, dict) and gps_coordinates.get("latitude") and gps_coordinates.get("longitude"):
                        lat = gps_coordinates["latitude"]
                        lon = gps_coordinates["longitude"]
                    else:
                        # Fallback to position field or search center coordinates
                        lat = position.get("latitude", latitude) if isinstance(position, dict) else latitude
                        lon = position.get("longitude", longitude) if isinstance(position, dict) else longitude
                    
                    business_info = {
                        "name": business.get("title"),
                        "address": business.get("address"),
                        "rating": business.get("rating"),
                        "reviews_count": business.get("reviews"),
                        "price": business.get("price"),
                        "type": business.get("type"),
                        "data_id": business.get("data_id"),
                        "latitude": lat,
                        "longitude": lon,
                        "position": position,
                        "gps_coordinates": gps_coordinates
                    }
                    nearby_businesses.append(business_info)
        
        logger.info(f"Found {len(nearby_businesses)} nearby {business_type} businesses")
        
        # Store in database
        if nearby_businesses:
            store_nearby_places(nearby_businesses, latitude, longitude)
        
        # Return updated state
        return {
            **state,
            "nearby_businesses": nearby_businesses,
            "current_step": "find_businesses_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in find businesses node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "nearby_businesses": [],
            "error": error_msg,
            "current_step": "find_businesses_error"
        }