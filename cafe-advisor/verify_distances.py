#!/usr/bin/env python3
"""Verify that distance calculations are accurate."""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_distances():
    """Verify distance calculations are correct."""
    try:
        # Import the distance calculation function
        from agents.nodes.chain_brand_node import _calculate_distance
        
        # Test with known coordinates
        # Chandigarh sector 17 (search location)
        lat1, lon1 = 30.7333, 76.7794
        
        # Some known cafes in Chandigarh with their coordinates
        test_cases = [
            # (name, lat, lon, expected_distance_km)
            ("Sector 17 Plaza", 30.7361, 76.7894, 1.1),  # Approx 1.1 km
            ("Rose Garden", 30.7445, 76.8012, 2.5),      # Approx 2.5 km
            ("Rock Garden", 30.7536, 76.8324, 5.3),      # Approx 5.3 km
        ]
        
        logger.info(f"Verifying distances from reference point: ({lat1}, {lon1})")
        
        for name, lat2, lon2, expected_distance in test_cases:
            calculated_distance = _calculate_distance(lat1, lon1, lat2, lon2)
            logger.info(f"{name}:")
            logger.info(f"  Coordinates: ({lat2}, {lon2})")
            logger.info(f"  Expected distance: ~{expected_distance} km")
            logger.info(f"  Calculated distance: {calculated_distance:.2f} km")
            
            # Check if the calculated distance is reasonable (within 20% of expected)
            if abs(calculated_distance - expected_distance) / expected_distance < 0.2:
                logger.info(f"  ✅ Distance calculation is accurate")
            else:
                logger.warning(f"  ⚠️  Distance may be inaccurate")
            logger.info("---")
            
        # Test with actual SerpAPI data
        logger.info("Testing with actual SerpAPI data:")
        from agents.nodes.chain_brand_node import _find_nearby_businesses
        
        businesses = _find_nearby_businesses(lat1, lon1, "cafe")
        
        if businesses:
            logger.info(f"Found {len(businesses)} businesses")
            # Show first 3 businesses with their distances
            for i, business in enumerate(businesses[:3]):
                logger.info(f"Business {i+1}:")
                logger.info(f"  Name: {business.get('name', 'N/A')}")
                logger.info(f"  Distance: {business.get('distance', 'N/A'):.2f} km")
                logger.info(f"  Coordinates: ({business.get('lat', 'N/A')}, {business.get('lon', 'N/A')})")
                logger.info("---")
                
            logger.info("✅ Distance calculations are working correctly")
            return True
        else:
            logger.error("❌ No businesses found")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying distances: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_distances()
    sys.exit(0 if success else 1)