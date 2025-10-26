"""Format output node for business advisor workflow."""

import logging
from typing import Dict, Any, List
from agents.state import BusinessAnalysisState

logger = logging.getLogger(__name__)


def format_output_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to format the final business analysis report.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with formatted output
    """
    logger.info("Starting format output node")
    
    try:
        # Extract information from state
        latitude = state["latitude"]
        longitude = state["longitude"]
        business_type = state["business_type"]
        area_name = state["area_name"]
        demographic_data = state["demographic_data"]
        # Use chain_brands instead of nearby_businesses for all businesses data
        all_businesses = state["chain_brands"]
        sentiment_analysis = state["sentiment_analysis"]
        llm_recommendation = state["llm_recommendation"]
        nearby_amenities = state.get("nearby_amenities", {})
        
        # Create formatted report
        report = {
            "property_details": {
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "business_type": business_type,
                "area_name": area_name,
                "demographics": demographic_data
            },
            "market_overview": _format_market_overview(all_businesses, sentiment_analysis),
            "recommendations": llm_recommendation,
            "top_competitors": _format_top_competitors(all_businesses, sentiment_analysis),
            "nearby_amenities": _format_amenities_section(nearby_amenities)
        }
        
        logger.info("Successfully formatted output report")
        
        # Return updated state
        return {
            **state,
            "formatted_output": report,
            "current_step": "format_output_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in format output node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "error": error_msg,
            "current_step": "format_output_error"
        }


def _format_market_overview(all_businesses: list, sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Format market overview section - WITH FIX FOR None VALUES."""
    business_count = len(all_businesses)
    
    # ⭐ THE FIX: Filter out None values before calculating average
    valid_ratings = [
        b.get("rating", 0) 
        for b in all_businesses 
        if b.get("rating") is not None  # This line prevents the error!
    ]
    avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0
    
    # Also handle None in sentiment data
    market_sentiment = sentiment_analysis.get("market_sentiment", {})
    avg_sentiment = market_sentiment.get("average_sentiment", 0) or 0
    positive_pct = market_sentiment.get("positive_percentage", 0) or 0
    negative_pct = market_sentiment.get("negative_percentage", 0) or 0
    
    return {
        "competitor_count": business_count,
        "average_rating": round(avg_rating, 2),
        "average_sentiment": round(avg_sentiment, 2),
        "positive_sentiment_percentage": round(positive_pct, 1),
        "negative_sentiment_percentage": round(negative_pct, 1)
    }


def _format_top_competitors(all_businesses: list, sentiment_analysis: Dict[str, Any]) -> list:
    """Format top competitors section - WITH FIX FOR None VALUES."""
    
    # ⭐ Filter out businesses without ratings
    valid_businesses = [
        b for b in all_businesses 
        if b.get("rating") is not None
    ]
    
    # Sort by rating and take top 3
    sorted_businesses = sorted(
        valid_businesses,
        key=lambda x: x.get("rating", 0),
        reverse=True
    )[:3]
    
    # Get sentiment data for businesses
    business_sentiments = {
        b.get("name", ""): b.get("metrics", {})
        for b in sentiment_analysis.get("business_sentiments", [])
    }
    
    top_competitors = []
    for business in sorted_businesses:
        name = business.get("name", "Unknown")
        sentiment_data = business_sentiments.get(name, {})
        
        competitor = {
            "name": name,
            "rating": business.get("rating", 0) or 0,
            "reviews_count": business.get("reviews_count", 0) or 0,
            "average_sentiment": round(sentiment_data.get("average_sentiment", 0) or 0, 2),
            "positive_percentage": round(sentiment_data.get("positive_percentage", 0) or 0, 1),
            "negative_percentage": round(sentiment_data.get("negative_percentage", 0) or 0, 1)
        }
        
        top_competitors.append(competitor)
    
    return top_competitors


def _format_amenities_section(amenities: Dict[str, List[Dict]]) -> str:
    """Format nearby amenities into readable insights."""
    
    if not amenities:
        return ""
    
    sections = ["\n## Nearby Amenities\n"]
    
    for amenity_type, places in amenities.items():
        if not places:
            continue
        
        sections.append(f"\n### {amenity_type.title()}s")
        sections.append(f"Found {len(places)} nearby {amenity_type}s:\n")
        
        for i, place in enumerate(places[:5], 1):
            name = place.get("name", "Unknown")
            address = place.get("address", "No address")
            rating = place.get("rating", "N/A")
            distance = place.get("distance", 0)
            
            sections.append(
                f"{i}. **{name}** ({distance:.2f} km away)\n"
                f"   - Address: {address}\n"
                f"   - Rating: {rating}\n"
            )
    
    return "".join(sections)