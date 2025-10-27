"""Intent understanding node for business advisor workflow."""

import logging
import re
import pandas as pd
import os
from typing import Dict, Any, Tuple, Optional
from agents.state import BusinessAnalysisState
from utils.api_clients import OpenAIClient

logger = logging.getLogger(__name__)


def intent_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to understand user intent and extract business type and property location from natural language query.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with extracted business type and coordinates
    """
    logger.info("Starting intent understanding node")
    
    try:
        # Get the business query from state
        business_query = state.get("business_query", "")
        
        if not business_query:
            logger.info("No business query provided, using default cafe and first property")
            # Load default coordinates
            latitude, longitude = _get_default_coordinates()
            
            # Get all business categories from settings
            from config.settings import BUSINESS_SEARCH_QUERIES
            all_business_categories = list(BUSINESS_SEARCH_QUERIES.keys())
            
            # Create default filters
            extracted_filters = {
                "business": all_business_categories,
                "primary_business": "cafe",
                "location": "Default Location",
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
            
            return {
                **state,
                "business_type": "cafe",
                "property_name": "Default Location",
                "latitude": latitude,
                "longitude": longitude,
                "query_type": "business_analysis",  # Default query type
                "extracted_filters": extracted_filters,
                "current_step": "intent_completed"
            }
        
        # Check if this is a branded store query
        query_type = _determine_query_type(business_query)
        
        # Extract business type and property name using LLM
        extracted_business_type, property_name = _extract_business_type_and_property(business_query)
        
        # Get coordinates for the property
        latitude, longitude = _get_coordinates_for_property(property_name)
        
        logger.info(f"Extracted business type: {extracted_business_type}, Property: {property_name}, Coordinates: {latitude}, {longitude}, Query type: {query_type}")
        
        # Get all business categories from settings
        from config.settings import BUSINESS_SEARCH_QUERIES
        all_business_categories = list(BUSINESS_SEARCH_QUERIES.keys())
        
        # Create extracted filters dictionary with ALL business categories
        extracted_filters = {
            "business": all_business_categories,  # All business types
            "primary_business": extracted_business_type,  # The one user asked about
            "location": property_name,  # Full location with city/area
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        
        logger.info(f"Extracted Filters: {extracted_filters}")
        
        # Return updated state
        return {
            **state,
            "business_type": extracted_business_type,
            "property_name": property_name,  # Add property_name to state
            "latitude": latitude,
            "longitude": longitude,
            "query_type": query_type,
            "extracted_filters": extracted_filters,  # Add explicit filters
            "current_step": "intent_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in intent understanding node: {str(e)}"
        logger.error(error_msg)
        # Fallback to default
        latitude, longitude = _get_default_coordinates()
        return {
            **state,
            "business_type": "cafe",
            "latitude": latitude,
            "longitude": longitude,
            "query_type": "business_analysis",  # Default query type
            "error": error_msg,
            "current_step": "intent_error"
        }


def _determine_query_type(query: str) -> str:
    """
    Determine the type of query (branded store lookup vs. business analysis).
    
    Args:
        query: User query
        
    Returns:
        Query type: "branded_store_lookup" or "business_analysis"
    """
    query_lower = query.lower()
    
    # Keywords that indicate a branded store lookup query
    branded_store_keywords = [
        "branded", "chain", "franchise", "brand", "chain store", 
        "franchise store", "tell me", "show me", "list", "find"
    ]
    
    # Keywords that indicate asking about specific branded business types
    business_type_keywords = [
        "shoe", "sneaker", "cafe", "coffee", "pharmacy", "grocery", 
        "clothing", "electronics", "restaurant"
    ]
    
    # Check if this is a branded store query
    is_branded_query = any(keyword in query_lower for keyword in branded_store_keywords)
    has_business_type = any(keyword in query_lower for keyword in business_type_keywords)
    
    if is_branded_query and has_business_type:
        return "branded_store_lookup"
    else:
        return "business_analysis"


def _extract_business_type_and_property(query: str) -> Tuple[str, str]:
    """
    Extract business type and property name from natural language query using LLM.
    
    Args:
        query: Natural language query from user
    
    Returns:
        Tuple of (business_type, property_name)
    """
    # Use LLM as the PRIMARY method for extraction
    prompt = f"""
Extract the business type and FULL property/location name from the following query:

Query: "{query}"

IMPORTANT: Extract the COMPLETE location name including city, area, or any additional location details.

Respond in JSON format:
{{
  "business_type": "extracted business type (e.g., cafe, mobile shop, electronics store, pharmacy, etc.)",
  "property_name": "FULL extracted property/location name with all details"
}}

Examples:
Query: "I want to open a coffee shop near Noble Aurellia"
Response: {{"business_type": "cafe", "property_name": "Noble Aurellia"}}

Query: "I want cafe near The Zirk, Zirakpur"
Response: {{"business_type": "cafe", "property_name": "The Zirk, Zirakpur"}}

Query: "I want to open Mobile shop near The Zirk"
Response: {{"business_type": "mobile shop", "property_name": "The Zirk"}}

Query: "Tell me branded shoe shop near VIP Road, Chandigarh"
Response: {{"business_type": "sneaker store", "property_name": "VIP Road, Chandigarh"}}
"""
    
    try:
        openai_client = OpenAIClient()
        response = openai_client.generate_recommendation(prompt)
        
        import json
        result = json.loads(response.strip())
        business_type = result.get("business_type", "").lower()
        property_name = result.get("property_name", "")
        
        # Normalize business type to match settings.py categories
        business_type = _normalize_business_type(business_type)
        
        logger.info(f"LLM extracted - Business: {business_type}, Property: {property_name}")
        return business_type, property_name
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}. Falling back to regex.")
        # Only use regex as FALLBACK if LLM fails
        return _extract_with_regex_fallback(query)


def _extract_property_name_simple(query: str) -> Optional[str]:
    """
    Simple pattern matching to extract property name from query.
    
    Args:
        query: User query
        
    Returns:
        Extracted property name or None
    """
    # Load property data
    try:
        # Get absolute path relative to project root
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(current_dir, "data", "property_project_lat_long.csv")
        
        if not os.path.exists(csv_path):
            csv_path = "data/property_project_lat_long.csv"
        
        df = pd.read_csv(csv_path)
        
        # Get unique project names and brand names
        project_names = df['project_name'].dropna().unique()
        brand_names = df['brand_name'].dropna().unique()
        
        query_lower = query.lower()
        
        # Check for project names
        for name in project_names:
            if isinstance(name, str) and name.lower() in query_lower:
                return name
        
        # Check for brand names
        for name in brand_names:
            if isinstance(name, str) and name.lower() in query_lower:
                return name
                
        return None
    except Exception as e:
        logger.error(f"Error extracting property name: {e}")
        return None


def _get_coordinates_for_property(property_name: str) -> Tuple[float, float]:
    """
    Get coordinates for a property name from the CSV file.
    
    Args:
        property_name: Name of the property
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if not property_name:
        logger.info("No property name provided, using default coordinates")
        return _get_default_coordinates()
    
    try:
        # Get absolute path relative to project root
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(current_dir, "data", "property_project_lat_long.csv")
        
        if not os.path.exists(csv_path):
            csv_path = "data/property_project_lat_long.csv"
        
        df = pd.read_csv(csv_path)
        
        logger.info(f"Searching for property: {property_name}")
        logger.info(f"CSV has {len(df)} rows")
        
        # Search for property by project_name or brand_name (case insensitive)
        matching_rows = df[
            (df['project_name'].str.lower() == property_name.lower()) |
            (df['brand_name'].str.lower() == property_name.lower())
        ]
        
        logger.info(f"Found {len(matching_rows)} matching rows")
        
        if not matching_rows.empty:
            first_row = matching_rows.iloc[0]
            lat = float(first_row['latitude'])
            lon = float(first_row['longitude'])
            logger.info(f"Found coordinates: {lat}, {lon}")
            return lat, lon
        else:
            logger.info("Property not found in CSV, using default coordinates")
            # Fallback to default coordinates
            return _get_default_coordinates()
            
    except Exception as e:
        logger.error(f"Error getting coordinates for property {property_name}: {e}")
        return _get_default_coordinates()


def _extract_with_regex_fallback(query: str) -> Tuple[str, str]:
    """
    Extract business type and property name using regex as fallback.
    
    Args:
        query: Natural language query from user
        
    Returns:
        Tuple of (business_type, property_name)
    """
    # Enhanced business types mapping with branded store keywords
    business_keywords = {
        "cafe|coffee": "cafe",
        "restaurant|dining": "restaurant",
        "shoe|sneaker": "sneaker store",
        "pharmacy|medicine": "pharmacy",
        "grocery|supermarket": "grocery shop",
        "clothing|apparel": "clothing store",
        "book": "bookstore",
        "electronics|tech": "electronics store",
        # Branded store specific keywords
        "branded.*shoe": "sneaker store",
        "branded.*store": "branded store"
    }
    
    # Try to match business type with regex first
    query_lower = query.lower()
    business_type = "cafe"  # default
    for pattern, bt in business_keywords.items():
        if re.search(pattern, query_lower):
            business_type = bt
            break
    
    # Try to extract property name with simple pattern matching
    property_name = _extract_property_name_simple(query)
    
    return business_type, property_name or ""


def _normalize_business_type(llm_business_type: str) -> str:
    """
    Normalize LLM-extracted business type to match BUSINESS_SEARCH_QUERIES keys.
    """
    normalization_map = {
        "mobile shop": "electronics store",
        "mobile store": "electronics store",
        "phone shop": "electronics store",
        "electronics shop": "electronics store",
        "coffee shop": "cafe",
        "grocery store": "grocery shop",
        "medical store": "pharmacy",
        "shoe shop": "sneaker store",
        "shoe store": "sneaker store",
        # Add more mappings as needed
    }
    
    return normalization_map.get(llm_business_type, llm_business_type)


def _get_default_coordinates() -> Tuple[float, float]:
    """
    Get default coordinates (first property in the dataset).
    
    Returns:
        Tuple of (latitude, longitude)
    """
    try:
        # Get absolute path relative to project root
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(current_dir, "data", "property_project_lat_long.csv")
        
        if not os.path.exists(csv_path):
            csv_path = "data/property_project_lat_long.csv"
        
        df = pd.read_csv(csv_path)
        if not df.empty:
            first_row = df.iloc[0]
            lat = float(first_row['latitude'])
            lon = float(first_row['longitude'])
            logger.info(f"Using default coordinates: {lat}, {lon}")
            return lat, lon
        else:
            # Hardcoded fallback
            logger.info("Using hardcoded fallback coordinates")
            return 30.6818636, 76.6924349  # NOBLE AURELLIA coordinates
    except Exception as e:
        logger.error(f"Error getting default coordinates: {e}")
        return 30.6818636, 76.6924349  # NOBLE AURELLIA coordinates