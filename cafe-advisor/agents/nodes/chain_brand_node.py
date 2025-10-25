"""Chain brand detection with city-wide local chain detection."""

import logging
from typing import Dict, Any, List
from agents.state import BusinessAnalysisState
from utils.city_chain_detector import CityChainDetector

logger = logging.getLogger(__name__)

def chain_brand_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """Find businesses and detect city-wide local chains."""
    logger.info("Starting chain brand detection with city-wide analysis")
    
    try:
        latitude = state["latitude"]
        longitude = state["longitude"]
        business_type = state["business_type"]
        
        logger.info(f"Finding all businesses near coordinates: {latitude}, {longitude} for {business_type}")
        
        # Use businesses already found in the previous step
        all_businesses = state.get("nearby_businesses", [])
        
        # Add distance information to businesses
        all_businesses = _add_distance_to_businesses(all_businesses, latitude, longitude)
        
        # NEW: Enrich businesses with city-wide chain information
        # This now also detects chains within the search results
        city_detector = CityChainDetector()
        enriched_businesses = city_detector.enrich_businesses_with_chain_data(all_businesses, business_type)
        
        # Add sentiment data and top reviews to businesses
        enriched_businesses = _add_sentiment_and_reviews(enriched_businesses, state.get("sentiment_analysis", {}), state.get("reviews_data", []))
        
        # Log chain detection results
        chain_count = sum(1 for b in enriched_businesses if b.get('is_local_chain', False))
        logger.info(f"Found {len(enriched_businesses)} businesses, {chain_count} are chains")
        
        # Return updated state
        return {
            **state,
            "chain_brands": enriched_businesses,
            "nearby_businesses": enriched_businesses,
            "current_step": "chain_brand_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in business detection node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "chain_brands": [],
            "nearby_businesses": [],
            "error": error_msg,
            "current_step": "chain_brand_error"
        }


def _add_distance_to_businesses(businesses: List[Dict], center_lat: float, center_lon: float) -> List[Dict]:
    """Add distance information to businesses."""
    from math import radians, sin, cos, sqrt, atan2
    
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    # Add distance to each business
    businesses_with_distance = []
    for business in businesses:
        business_copy = business.copy()
        
        # Get business coordinates
        lat = business.get('latitude', center_lat)
        lon = business.get('longitude', center_lon)
        
        # Calculate distance
        distance = _calculate_distance(center_lat, center_lon, lat, lon)
        business_copy['distance'] = distance
        
        # Also add lat/lon fields with standard names for consistency
        business_copy['lat'] = lat
        business_copy['lon'] = lon
        
        businesses_with_distance.append(business_copy)
    
    return businesses_with_distance


def _find_nearby_businesses(latitude: float, longitude: float, business_type: str) -> List[Dict]:
    """
    Find nearby businesses of specified type.
    
    Args:
        latitude: Latitude of search center
        longitude: Longitude of search center
        business_type: Type of business to search for
        
    Returns:
        List of nearby businesses
    """
    # For the chain brand node, we'll use the businesses already found in the previous step
    # This function is kept for API compatibility but doesn't perform a new search
    return []


def _add_sentiment_and_reviews(businesses: List[Dict], sentiment_analysis: Dict, reviews_data: List[Dict]) -> List[Dict]:
    """
    Add sentiment data and top positive/negative reviews to businesses.
    
    Args:
        businesses: List of businesses
        sentiment_analysis: Sentiment analysis data
        reviews_data: Raw reviews data
        
    Returns:
        Enriched businesses with sentiment and review data
    """
    # Create a mapping of business names to sentiment metrics
    business_sentiments = {}
    for business_sentiment in sentiment_analysis.get("business_sentiments", []):
        name = business_sentiment.get("business_name", "")
        business_sentiments[name] = business_sentiment.get("metrics", {})
    
    # Group reviews by business name
    from collections import defaultdict
    business_reviews = defaultdict(list)
    for review in reviews_data:
        business_name = review.get("business_name", "Unknown")
        business_reviews[business_name].append(review)
    
    # Add sentiment data and top reviews to each business
    enriched_businesses = []
    for business in businesses:
        business_copy = business.copy()
        
        # Add sentiment metrics
        business_name = business.get("name", "Unknown")
        sentiment_metrics = business_sentiments.get(business_name, {})
        
        # Add sentiment data to business
        business_copy["rating"] = business.get("rating", 0) or 0
        business_copy["reviews_count"] = business.get("reviews_count", 0) or 0
        business_copy["positive_percentage"] = sentiment_metrics.get("positive_percentage", 0)
        business_copy["negative_percentage"] = sentiment_metrics.get("negative_percentage", 0)
        business_copy["average_sentiment"] = sentiment_metrics.get("average_sentiment", 0)
        
        # Get reviews for this business
        reviews = business_reviews.get(business_name, [])
        
        # Filter and sort reviews by sentiment
        positive_reviews = [r for r in reviews if r.get("sentiment", {}).get("label") == "positive"]
        negative_reviews = [r for r in reviews if r.get("sentiment", {}).get("label") == "negative"]
        
        # Sort by compound score (most positive/negative first)
        positive_reviews.sort(key=lambda r: r.get("sentiment", {}).get("compound", 0), reverse=True)
        negative_reviews.sort(key=lambda r: r.get("sentiment", {}).get("compound", 0))
        
        # Add top 2 positive and negative reviews
        business_copy["positive_reviews"] = positive_reviews[:2]
        business_copy["negative_reviews"] = negative_reviews[:2]
        
        enriched_businesses.append(business_copy)
    
    return enriched_businesses