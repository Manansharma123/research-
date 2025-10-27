"""LLM-based brand detection for identifying branded vs local businesses."""

import logging
from typing import Dict, Any, List
from utils.api_clients import PerplexityClient

logger = logging.getLogger(__name__)

class LLMBrandDetector:
    """Uses Perplexity AI to intelligently identify branded vs local businesses."""
    
    def __init__(self):
        """Initialize the LLM brand detector with Perplexity AI."""
        self.perplexity_client = PerplexityClient()
        logger.info("LLM Brand Detector initialized with Perplexity AI")
    
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
            
            # Get Perplexity AI response
            response = self.perplexity_client.generate_recommendation(prompt)
            
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
You are an expert business analyst with access to real-time online search, specializing in identifying branded chains vs local independent businesses in India.

🎯 TASK: Analyze the following business and determine if it's a BRANDED CHAIN or a LOCAL INDEPENDENT business:

Business Name: {business_name}
Business Type: {business_type}
Location Context: {location_context}

🔍 INSTRUCTIONS:
1. Use your online search capability to verify if this business is part of a known chain/franchise
2. Check for multiple locations, franchise information, or corporate ownership
3. Determine if it's a branded chain (part of a larger franchise/chain) or a local independent business
4. If it's a branded chain, identify the official brand name
5. Provide a confidence score (0.0 to 1.0) based on your findings
6. Explain your reasoning with specific evidence

⚠️ IMPORTANT: Be STRICT in classification:
- Only mark as "branded" if you can confirm it's part of a known chain/franchise with multiple locations
- If uncertain or if it appears to be a single location business, classify as "local"
- Local businesses may have professional names but are NOT part of chains

✅ Examples of BRANDED chains in India:
- CCD (Cafe Coffee Day) - branded cafe chain with 1000+ outlets
- Starbucks - international branded cafe chain
- McDonald's - international fast food chain
- Domino's - pizza chain
- Haldiram's - branded restaurant/snack chain
- Bata - branded shoe store chain
- Reliance Fresh - branded retail chain

❌ Examples of LOCAL independent businesses:
- Sharma's Cafe - local cafe (single location)
- Mohali Book Corner - local bookstore
- Family Shoe Store - local shoe store
- Raj Restaurant - local restaurant
- City Bakery - local bakery

📋 RESPONSE FORMAT (JSON only):
{{
  "is_branded": true/false,
  "brand_name": "official brand name if branded, or original name if local",
  "confidence": 0.0-1.0,
  "reasoning": "specific evidence from online search or analysis",
  "classification_type": "branded/local"
}}

Use your online search to verify the business and provide accurate classification.
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