"""Geocoding utility using geopy."""

import time
from geopy.geocoders import Nominatim
from typing import Dict, Any, Optional


class Geocoder:
    """Wrapper for geopy geocoding functionality."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="business-advisor")
        
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Convert coordinates to address information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with address information
        """
        try:
            time.sleep(1)  # Rate limiting
            location = self.geolocator.reverse(f"{latitude}, {longitude}")
            
            if location and location.raw:
                address = location.raw.get('address', {})
                return {
                    'area_name': self._extract_area_name(address),
                    'city': address.get('city') or address.get('town') or address.get('village'),
                    'state': address.get('state'),
                    'country': address.get('country'),
                    'full_address': location.address
                }
            else:
                return {
                    'area_name': 'Unknown',
                    'city': 'Unknown',
                    'state': 'Unknown',
                    'country': 'Unknown',
                    'full_address': 'Unknown'
                }
        except Exception as e:
            raise Exception(f"Error in reverse geocoding: {str(e)}")
            
    def _extract_area_name(self, address: Dict[str, Any]) -> str:
        """
        Extract area name from address components.
        
        Args:
            address: Address components dictionary
            
        Returns:
            Area name string
        """
        # Try to extract the most specific area name available
        area_name = (address.get('neighbourhood') or 
                    address.get('suburb') or 
                    address.get('quarter') or 
                    address.get('residential') or
                    address.get('city_district') or
                    address.get('borough') or
                    address.get('municipality') or
                    address.get('town') or
                    address.get('village') or
                    'Unknown')
                    
        return area_name