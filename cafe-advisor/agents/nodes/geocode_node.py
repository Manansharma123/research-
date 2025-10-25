"""Geocode node for business advisor workflow."""

import logging
import pandas as pd
import os
from typing import Dict, Any
from agents.state import BusinessAnalysisState
from utils.geocoder import Geocoder

logger = logging.getLogger(__name__)


def geocode_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to geocode property coordinates to area names.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with area name information
    """
    logger.info("Starting geocode node")
    
    try:
        # Extract coordinates from state
        latitude = state["latitude"]
        longitude = state["longitude"]
        
        logger.info(f"Geocoding coordinates: {latitude}, {longitude}")
        
        # First, try to find a matching property in the CSV
        area_name = _lookup_property_in_csv(latitude, longitude)
        
        logger.info(f"CSV lookup result: {area_name}")
        
        if area_name and area_name != 'Unknown':
            logger.info(f"Found property in CSV: {area_name}")
            return {
                **state,
                "area_name": area_name,
                "current_step": "geocode_completed"
            }
        
        # If not found in CSV, use geocoder for reverse geocoding
        logger.info("Property not found in CSV, using geocoder for reverse geocoding")
        try:
            geocoder = Geocoder()
            location_info = geocoder.reverse_geocode(latitude, longitude)
            
            logger.info(f"Successfully geocoded to area: {location_info['area_name']}")
            
            # Return updated state
            return {
                **state,
                "area_name": location_info["area_name"],
                "current_step": "geocode_completed"
            }
        except Exception as geocode_error:
            logger.error(f"Error in reverse geocoding: {geocode_error}")
            # If geocoding fails, still return with area_name as Unknown
            return {
                **state,
                "area_name": "Unknown",
                "current_step": "geocode_completed"
            }
        
    except Exception as e:
        error_msg = f"Error in geocode node: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "area_name": "Unknown",
            "error": error_msg,
            "current_step": "geocode_error"
        }


def _lookup_property_in_csv(latitude: float, longitude: float) -> str:
    """
    Look up property name in CSV file based on coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Property name if found, 'Unknown' otherwise
    """
    try:
        # Load the property data CSV
        # Get the directory of this file and construct path relative to project root
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(current_dir, "data", "property_project_lat_long.csv")
        
        if not os.path.exists(csv_path):
            # Fallback to relative path
            csv_path = "data/property_project_lat_long.csv"
            
        if not os.path.exists(csv_path):
            logger.warning(f"Property CSV file not found at {csv_path}")
            return "Unknown"
        
        df = pd.read_csv(csv_path)
        
        logger.debug(f"Loaded CSV with {len(df)} rows for lookup")
        logger.debug(f"Looking for coordinates: {latitude}, {longitude}")
        
        # Look for exact coordinate match (with small tolerance for floating point comparison)
        tolerance = 0.000001  # About 10cm tolerance
        
        # Log the first few rows for debugging
        logger.debug("First few CSV rows:")
        for i in range(min(3, len(df))):
            logger.debug(f"Row {i}: {df.iloc[i]['latitude']}, {df.iloc[i]['longitude']}, {df.iloc[i].get('project_name', 'N/A')}")
        
        matching_rows = df[
            (abs(df['latitude'] - latitude) < tolerance) &
            (abs(df['longitude'] - longitude) < tolerance)
        ]
        
        logger.debug(f"Found {len(matching_rows)} matching rows")
        
        if not matching_rows.empty:
            # Return the first matching property name
            first_match = matching_rows.iloc[0]
            property_name = first_match.get('project_name') or first_match.get('brand_name')
            logger.debug(f"Found property name: {property_name}")
            if property_name:
                return property_name
        
        logger.debug("No matching property found in CSV")
        return "Unknown"
    except Exception as e:
        logger.error(f"Error looking up property in CSV: {e}")
        return "Unknown"