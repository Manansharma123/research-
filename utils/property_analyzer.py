"""Property analyzer for generating pros, cons, and suggestions based on property features."""

import pandas as pd
import json
import logging
import os
from typing import Dict, Any, Optional, List
from utils.api_clients import OpenAIClient

logger = logging.getLogger(__name__)


class PropertyAnalyzer:
    """Analyzes property features from CSV to generate business recommendations."""
    
    def __init__(self):
        """Initialize the property analyzer."""
        self.openai_client = OpenAIClient()
        self.property_data = self._load_property_data()
        logger.info("Property Analyzer initialized")
    
    def _load_property_data(self) -> pd.DataFrame:
        """
        Load property data from CSV.
        
        Returns:
            DataFrame with property data
        """
        try:
            # Get the directory of this file and construct path relative to project root
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            csv_path = os.path.join(current_dir, "data", "dummy_property_variables.csv")
            
            if not os.path.exists(csv_path):
                # Fallback to relative path
                csv_path = "data/dummy_property_variables.csv"
            
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded property data with {len(df)} records from {csv_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading property data: {e}")
            return pd.DataFrame()
    
    def find_property_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Find property data by coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with property data or None if not found
        """
        if self.property_data.empty:
            return None
            
        try:
            # Look for matching coordinates
            for _, row in self.property_data.iterrows():
                lat_long_str = row['Lat-Long']
                try:
                    # Parse the coordinate string
                    coords = lat_long_str.replace('"', '').strip()
                    if ',' in coords:
                        lat, lon = coords.split(',')
                        lat_val = float(lat.strip())
                        lon_val = float(lon.strip())
                        
                        # Check if coordinates match (with small tolerance)
                        tolerance = 0.000001
                        if abs(lat_val - latitude) < tolerance and abs(lon_val - longitude) < tolerance:
                            # Convert row to dictionary
                            property_info = row.to_dict()
                            logger.info(f"Found property data for coordinates: {latitude}, {longitude}")
                            return property_info
                except Exception as parse_error:
                    logger.debug(f"Error parsing coordinates {lat_long_str}: {parse_error}")
                    continue
                    
            logger.info(f"No property data found for coordinates: {latitude}, {longitude}")
            return None
        except Exception as e:
            logger.error(f"Error finding property by coordinates: {e}")
            return None
    
    def generate_property_analysis(self, business_type: str, area_name: str, 
                                 latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Generate pros, cons, and suggestions based on property features.
        
        Args:
            business_type: Type of business to analyze
            area_name: Name of the area
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with pros, cons, suggestions, and recommendation
        """
        try:
            # Find property data by coordinates
            property_data = self.find_property_by_coordinates(latitude, longitude)
            
            if not property_data:
                # Return fallback analysis if no property data found
                return self._generate_fallback_analysis(business_type, area_name)
            
            # Create prompt for LLM
            prompt = self._create_property_analysis_prompt(business_type, area_name, property_data)
            
            # Generate analysis using LLM
            response = self.openai_client.generate_recommendation(prompt)
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response.replace("```json", "").replace("```", ""))
                logger.info(f"Generated property analysis for {business_type} in {area_name}")
                return analysis_data
            except json.JSONDecodeError:
                logger.error("Error parsing LLM response as JSON")
                return self._generate_fallback_analysis(business_type, area_name)
                
        except Exception as e:
            logger.error(f"Error generating property analysis: {e}")
            return self._generate_fallback_analysis(business_type, area_name)
    
    def _create_property_analysis_prompt(self, business_type: str, area_name: str, 
                                       property_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the LLM to generate property-based analysis.
        
        Args:
            business_type: Type of business to analyze
            area_name: Name of the area
            property_data: Property data from CSV
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are a business consultant expert in evaluating market opportunities. Analyze the feasibility of opening a {business_type} at the location "{area_name}" based on the detailed property features provided.

PROPERTY FEATURES:
{json.dumps(property_data, indent=2)}

INSTRUCTIONS:
Based on these property features, provide a detailed analysis for opening a {business_type} at this location. Focus on how these specific demographic and market characteristics affect the business opportunity.

Provide your analysis in JSON format with the following keys:
1. "pros" - List 4-5 specific opportunities/benefits based on the property features
2. "cons" - List 4-5 specific challenges/risk factors based on the property features
3. "suggestions" - List 6-7 actionable strategies to maximize success given these property features
4. "recommendation" - One sentence summary recommendation

RESPONSE FORMAT:
{{
  "pros": ["specific opportunity 1 based on property features", "specific opportunity 2 based on property features", ...],
  "cons": ["specific challenge 1 based on property features", "specific challenge 2 based on property features", ...],
  "suggestions": ["actionable strategy 1 based on property features", "actionable strategy 2 based on property features", ...],
  "recommendation": "one sentence summary recommendation based on property features"
}}

Be specific and data-driven in your analysis. Reference the actual property feature values in your response. For example:
- Instead of "High income area", say "Area has X households with income above 10 LPA"
- Instead of "High foot traffic", say "Area has a footfall score of X"
- Instead of "Young population", say "Area has X people in 18-60 age group"

Focus on how these specific characteristics make this location suitable or challenging for a {business_type}.
"""
        
        return prompt.strip()
    
    def _generate_fallback_analysis(self, business_type: str, area_name: str) -> Dict[str, Any]:
        """
        Generate fallback analysis when property data is not available.
        
        Args:
            business_type: Type of business to analyze
            area_name: Name of the area
            
        Returns:
            Dictionary with fallback analysis
        """
        return {
            "pros": [
                f"Location identified as {area_name}",
                "Demographic data available for analysis",
                "Market research completed",
                "Competitor analysis performed"
            ],
            "cons": [
                "Unable to access detailed property features",
                "Limited demographic insights",
                "Generic analysis without location-specific data"
            ],
            "suggestions": [
                f"Manually research the {business_type} market in {area_name}",
                "Visit the location to assess foot traffic",
                "Survey potential customers in the area",
                "Analyze competitor offerings in the vicinity",
                "Consider property rental costs and terms",
                "Evaluate accessibility and parking availability",
                "Check local regulations and permits required"
            ],
            "recommendation": f"Further analysis required for {business_type} opportunity in {area_name}"
        }