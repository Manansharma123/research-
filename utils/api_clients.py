"""API clients for business advisor system."""

import time
import requests
from typing import Dict, Any, Optional, List
from config.settings import (
    SERPAPI_KEY, SERPAPI_BASE_URL, REQUEST_DELAY, 
    OPENAI_API_KEY, OPENAI_MODEL,
    PERPLEXITY_API_KEY, PERPLEXITY_MODEL
)
from openai import OpenAI


class SerpApiClient:
    """Client for interacting with SerpApi."""
    
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = SERPAPI_BASE_URL
        
    def search_places(self, query: str, latitude: float, longitude: float, 
                     radius: int = 1000) -> Dict[str, Any]:
        """
        Search for places near given coordinates.
        
        Args:
            query: Search query (e.g., "cafe", "sneaker store")
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius: Search radius in meters (default: 1000)
            
        Returns:
            Dictionary with search results
        """
        params = {
            "engine": "google_maps",
            "q": query,
            "ll": f"@{latitude},{longitude},{radius}m",  # Correct format with radius
            "api_key": self.api_key,
            "type": "search"
        }
        
        try:
            time.sleep(REQUEST_DELAY)  # Rate limiting
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error searching places: {str(e)}")
    
    # NEW METHOD: Search for multiple amenities
    def search_amenities(self, amenity_types: List[str], latitude: float, 
                        longitude: float, radius: int = 5000) -> Dict[str, List[Dict]]:
        """
        Search for multiple amenity types near given coordinates.
        
        Args:
            amenity_types: List of amenity types (e.g., ["hospital", "school"])
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius: Search radius in meters (default: 5000)
            
        Returns:
            Dictionary mapping amenity types to their search results
        """
        results = {}
        
        for amenity_type in amenity_types:
            try:
                search_results = self.search_places(
                    query=f"{amenity_type}s near me",
                    latitude=latitude,
                    longitude=longitude,
                    radius=radius
                )
                results[amenity_type] = search_results.get("local_results", [])
            except Exception as e:
                print(f"Error searching for {amenity_type}: {e}")
                results[amenity_type] = []
        
        return results
    
    def get_place_reviews(self, data_id: str, next_page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get reviews for a specific place.
        
        Args:
            data_id: SerpApi data_id for the place
            next_page_token: Token for pagination (optional)
            
        Returns:
            Dictionary with reviews data including 'reviews' and 'serpapi_pagination'
        """
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "api_key": self.api_key,
            "sort_by": "newestFirst"  # Get newest reviews first
        }
        
        # Add pagination token if provided
        if next_page_token:
            params["next_page_token"] = next_page_token
        
        try:
            time.sleep(REQUEST_DELAY)  # Rate limiting
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error fetching reviews: {str(e)}")


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        
    def generate_recommendation(self, prompt: str) -> str:
        """
        Generate business recommendations using OpenAI LLM.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            Generated recommendation text
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating recommendation: {str(e)}")
    
    def generate_brand_classification(self, prompt: str) -> str:
        """
        Generate brand classification using OpenAI LLM.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            Generated brand classification text
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.1,  # Lower temperature for more consistent classifications
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating brand classification: {str(e)}")


class PerplexityClient:
    """Client for interacting with Perplexity API for intelligent recommendations."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
        self.model = PERPLEXITY_MODEL
        
    def generate_recommendation(self, prompt: str) -> str:
        """
        Generate intelligent business recommendations using Perplexity LLM.
        Perplexity provides more insightful analysis with real-time online search.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            Generated recommendation text in JSON format
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business analysis expert providing detailed, insightful recommendations for business opportunities. Always respond in valid JSON format with keys: pros, cons, suggestions, and recommendation."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating Perplexity recommendation: {str(e)}")