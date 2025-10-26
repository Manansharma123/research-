"""State definition for the business opportunity analysis workflow."""

from typing import TypedDict, List, Dict, Any

class BusinessAnalysisState(TypedDict):
    """State that flows through the LangGraph workflow."""
    
    # Input data
    business_query: str
    business_type: str
    demographic_data: Dict[str, Any]
    
    # Node outputs
    latitude: float
    longitude: float
    area_name: str
    property_name: str  # Full property/location name
    nearby_businesses: List[Dict[str, Any]]
    reviews_data: List[Dict[str, Any]]
    sentiment_analysis: Dict[str, Any]
    llm_recommendation: Dict[str, Any]
    chain_brands: List[Dict[str, Any]]  # Now contains all businesses, not just chain brands
    nearby_amenities: Dict[str, List[Dict[str, Any]]]  # NEW: Nearby amenities by type
    chart_data: Dict[str, Any]  # NEW: Interactive chart data for visualization
    
    # Extracted filters (NEW)
    extracted_filters: Dict[str, Any]  # Contains business types, location, coordinates
    
    # Scraped data (NEW)
    scraped_data: List[Dict[str, Any]]  # Real-time web-scraped data
    scraper_executed: bool
    
    # Query type
    query_type: str
    
    # Workflow metadata
    current_step: str
    error: str
    messages: List[str]