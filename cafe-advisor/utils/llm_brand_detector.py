"""LLM-based brand detection for identifying branded vs local businesses."""

import logging
from typing import Dict, Any, List
from utils.api_clients import OpenAIClient

logger = logging.getLogger(__name__)

class LLMBrandDetector:
    """Uses LLM to intelligently identify branded vs local businesses."""
    
    def __init__(self):
        """Initialize the LLM brand detector."""
        self.openai_client = OpenAIClient()
        logger.info("LLM Brand Detector initialized")
    
    def identify_brand_status(self, business_name: str, business_type: str = "business", 
                            location_context: str = "") -> Dict[str, Any]:
        """
        Use LLM to determine if a business is branded or local.
        
        Args:
            business_name: Name of the business
            business_type: Type of business (cafe, shoe store, etc.)
            location_context: Context about the location/area
            
        Returns:
            Dictionary with brand classification and confidence
        """
        try:
            # Create prompt for LLM
            prompt = self._create_brand_identification_prompt(
                business_name, business_type, location_context
            )
            
            # Get LLM response
            response = self.openai_client.generate_brand_classification(prompt)
            
            # Parse response
            return self._parse_brand_response(response)
            
        except Exception as e:
            logger.error(f"Error in LLM brand detection for {business_name}: {e}")
            # Fallback to default classification
            return {
                "is_branded": False,
                "brand_name": business_name,
                "confidence": 0.5,
                "reasoning": "Fallback classification due to error",
                "classification_type": "local"
            }
    
    def batch_identify_brands(self, businesses: List[Dict], 
                            business_type: str = "business") -> List[Dict]:
        """
        Batch process multiple businesses for brand identification.
        
        Args:
            businesses: List of business dictionaries
            business_type: Type of business for context
            
        Returns:
            List of businesses with brand classification added
        """
        classified_businesses = []
        
        for business in businesses:
            business_name = business.get('name', '')
            location_context = business.get('area_name', '')
            
            # Get brand classification
            brand_info = self.identify_brand_status(
                business_name, business_type, location_context
            )
            
            # Add classification to business
            business_copy = business.copy()
            business_copy.update(brand_info)
            classified_businesses.append(business_copy)
        
        return classified_businesses
    
    def _create_brand_identification_prompt(self, business_name: str, 
                                          business_type: str, 
                                          location_context: str) -> str:
        """
        Create a prompt for LLM to classify a business as branded or local.
        
        Args:
            business_name: Name of the business
            business_type: Type of business
            location_context: Context about location
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are an expert business analyst specializing in identifying branded chains vs local independent businesses.

Analyze the following business and determine if it's a branded chain or a local independent business:

Business Name: {business_name}
Business Type: {business_type}
Location Context: {location_context}

Instructions:
1. Determine if this is a branded chain (part of a larger franchise/chain) or a local independent business
2. If it's a branded chain, identify the brand name
3. Provide a confidence score (0.0 to 1.0) in your classification
4. Explain your reasoning in 1-2 sentences

Examples of branded chains:
- CCD (Cafe Coffee Day) - branded cafe chain
- Starbucks - branded cafe chain
- McDonald's - branded restaurant chain
- Skechers - branded shoe store chain
- Nike - branded sportswear chain

Examples of local independent businesses:
- Sharma's Cafe - local cafe
- Mohali Book Corner - local bookstore
- Family Shoe Store - local shoe store

Respond in JSON format with these keys:
- "is_branded": boolean (true if branded chain, false if local)
- "brand_name": string (the brand name if branded, or original name if local)
- "confidence": number (0.0 to 1.0)
- "reasoning": string (1-2 sentence explanation)
- "classification_type": string ("branded" or "local")

RESPONSE FORMAT:
{{
  "is_branded": true/false,
  "brand_name": "brand name",
  "confidence": 0.0-1.0,
  "reasoning": "explanation",
  "classification_type": "branded/local"
}}
"""
        return prompt.strip()
    
    def _parse_brand_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response for brand classification.
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed brand classification dictionary
        """
        try:
            import json
            
            # Clean and parse JSON response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]  # Remove ```json
            if response.endswith("```"):
                response = response[:-3]  # Remove ```
            
            parsed = json.loads(response)
            
            # Ensure all required fields are present
            return {
                "is_branded": bool(parsed.get("is_branded", False)),
                "brand_name": str(parsed.get("brand_name", "")),
                "confidence": float(parsed.get("confidence", 0.5)),
                "reasoning": str(parsed.get("reasoning", "No reasoning provided")),
                "classification_type": str(parsed.get("classification_type", "local"))
            }
        except Exception as e:
            logger.error(f"Error parsing brand response: {e}")
            # Return default classification
            return {
                "is_branded": False,
                "brand_name": "",
                "confidence": 0.5,
                "reasoning": "Error in parsing response",
                "classification_type": "local"
            }