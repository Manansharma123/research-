"""Extract reviews node for business advisor workflow."""

import logging
from typing import Dict, Any
from agents.state import BusinessAnalysisState
from utils.api_clients import SerpApiClient
from utils.database import store_serp_reviews, get_serp_reviews, get_cached_business_ids

logger = logging.getLogger(__name__)

def extract_reviews_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to extract reviews for nearby businesses.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with reviews data
    """
    logger.info("Starting extract reviews node")
    
    try:
        # Extract nearby businesses from state
        nearby_businesses = state["nearby_businesses"]
        latitude = state["latitude"]
        longitude = state["longitude"]
        
        # Check if we have businesses
        if not nearby_businesses:
            logger.info("No businesses found, skipping review extraction")
            return {
                **state,
                "reviews_data": [],
                "current_step": "extract_reviews_completed"
            }
        
        # Initialize SerpApi client
        serp_client = SerpApiClient()
        
        # Extract reviews for each business (limit to top 10 businesses, max 20 reviews each)
        reviews_data = []
        
        for i, business in enumerate(nearby_businesses[:10]):
            data_id = business.get("data_id")
            business_name = business.get("name", "Unknown")
            business_lat = business.get("latitude", latitude)
            business_lon = business.get("longitude", longitude)
            
            if not data_id:
                logger.warning(f"No data_id for business: {business_name}")
                continue
            
            logger.info(f"[{i+1}/10] Processing reviews for: {business_name} (ID: {data_id})")
            
            # Fetch reviews from API (no caching, limit to 20 reviews per business)
            logger.info(f"  → Fetching reviews from API (max 20 reviews)")
            
            # Collect reviews (limit to 20)
            all_reviews = []
            
            try:
                # Get reviews for the business
                review_response = serp_client.get_place_reviews(data_id)
                reviews = review_response.get("reviews", [])
                
                # Limit to 20 reviews total
                if len(reviews) > 20:
                    reviews = reviews[:20]
                
                all_reviews.extend(reviews)
                logger.info(f"  - Got {len(all_reviews)} reviews (limited to 20)")
                
                # Add business context to each review
                for review in all_reviews:
                    review["business_name"] = business_name
                    review["business_rating"] = business.get("rating")
                    review["business_address"] = business.get("address")
                
                reviews_data.extend(all_reviews)
                
                # Store reviews in database
                store_serp_reviews(business_name, data_id, all_reviews, business_lat, business_lon)
                
            except Exception as e:
                logger.warning(f"  ✗ Error extracting reviews for {business_name}: {str(e)}")
                continue
        
        logger.info(f"Completed: Extracted/used {len(reviews_data)} total reviews from {min(10, len(nearby_businesses))} businesses")
        
        return {
            **state,
            "reviews_data": reviews_data,
            "current_step": "extract_reviews_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in extract reviews node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "reviews_data": [],
            "error": error_msg,
            "current_step": "extract_reviews_error"
        }