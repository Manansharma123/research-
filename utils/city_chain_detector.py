"""City-wide local chain detection system."""

import logging
import pandas as pd
import os
from typing import Dict, List, Any
from collections import defaultdict
import re
from difflib import SequenceMatcher
from math import radians, sin, cos, sqrt, atan2
from utils.llm_brand_detector import LLMBrandDetector

logger = logging.getLogger(__name__)

class CityChainDetector:
    """Detects local chains across the entire city using a master database."""
    
    def __init__(self, city_database_path: str = None):
        """
        Initialize with city-wide business database.
        
        Args:
            city_database_path: Path to CSV with all city businesses
        """
        if city_database_path is None:
            # Get absolute path relative to project root
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            city_database_path = os.path.join(current_dir, "data", "city_businesses.csv")
        
        self.city_database_path = city_database_path
        self.city_businesses_df = self._load_city_database()
        self.chain_cache = self._build_chain_index()
        self.llm_brand_detector = LLMBrandDetector()
        logger.info(f"City chain detector initialized with {len(self.city_businesses_df)} businesses")
    
    def _load_city_database(self) -> pd.DataFrame:
        """Load city-wide business database."""
        if os.path.exists(self.city_database_path):
            try:
                df = pd.read_csv(self.city_database_path)
                logger.info(f"Loaded city database: {len(df)} businesses")
                return df
            except Exception as e:
                logger.error(f"Failed to load city database: {e}")
        
        logger.warning("No city database found - creating empty dataframe")
        return pd.DataFrame(columns=['name', 'lat', 'lon', 'address', 'types'])
    
    def _build_chain_index(self) -> Dict[str, List[Dict]]:
        """
        Build an index of all chains in the city.
        Returns: {normalized_brand_name: [locations]}
        """
        chain_index = defaultdict(list)
        
        for _, row in self.city_businesses_df.iterrows():
            name = row.get('name', '')
            if not name:
                continue
            
            # Normalize the brand name
            normalized = self._normalize_brand_name(name)
            
            chain_index[normalized].append({
                'original_name': name,
                'lat': row.get('lat'),
                'lon': row.get('lon'),
                'address': row.get('address', ''),
                'types': row.get('types', '')
            })
        
        # Filter to only businesses with 2+ locations (local chains)
        local_chains = {
            brand: locations 
            for brand, locations in chain_index.items() 
            if len(locations) >= 2
        }
        
        logger.info(f"Found {len(local_chains)} local chains in city database")
        return local_chains
    
    def check_if_chain(self, business_name: str) -> Dict[str, Any]:
        """
        Check if a business is part of a local chain.
        
        Args:
            business_name: Name of the business
            
        Returns:
            Chain information if it's a local chain, None otherwise
        """
        normalized = self._normalize_brand_name(business_name)
        
        if normalized in self.chain_cache:
            locations = self.chain_cache[normalized]
            return {
                'is_local_chain': True,
                'chain_name': normalized.title(),
                'total_locations': len(locations),
                'locations': locations,
                'description': f"Local chain with {len(locations)} branches across the city"
            }
        
        return {
            'is_local_chain': False,
            'chain_name': None,
            'total_locations': 1,
            'description': "Independent single-location business"
        }
    
    def detect_chains_in_results(self, businesses: List[Dict], similarity_threshold: float = 0.85) -> Dict[str, List[Dict]]:
        """
        Detect local chains within the search results themselves.
        This identifies businesses with same or similar names at different locations.
        
        Args:
            businesses: List of nearby businesses
            similarity_threshold: Minimum similarity score for name matching (default: 0.85)
            
        Returns:
            Dictionary of detected local chains from the results
        """
        if not businesses:
            return {}
        
        # Group businesses by normalized name
        name_groups = defaultdict(list)
        for business in businesses:
            name = business.get('name', '')
            if name:
                normalized = self._normalize_brand_name(name)
                name_groups[normalized].append(business)
        
        # Also check for similar names using fuzzy matching
        result_chains = defaultdict(list)
        processed = set()
        
        for normalized_name, group in name_groups.items():
            if normalized_name in processed:
                continue
            
            # Start with exact matches
            cluster = group.copy()
            cluster_names = [business.get('name', '') for business in group]
            
            # Check for similar names
            for other_normalized, other_group in name_groups.items():
                if other_normalized == normalized_name or other_normalized in processed:
                    continue
                
                # Calculate similarity between normalized names
                similarity = SequenceMatcher(None, normalized_name, other_normalized).ratio()
                
                if similarity >= similarity_threshold:
                    # Check if locations are different (at least 0.5km apart)
                    if self._are_different_locations(cluster, other_group):
                        cluster.extend(other_group)
                        cluster_names.extend([business.get('name', '') for business in other_group])
                        processed.add(other_normalized)
            
            # Only consider as chain if there are at least 2 locations
            if len(cluster) >= 2:
                # Use the most common name as the chain name
                name_counts = defaultdict(int)
                for name in cluster_names:
                    if name:
                        name_counts[name] += 1
                
                if name_counts:
                    chain_name = max(name_counts.items(), key=lambda x: x[1])[0]
                    result_chains[chain_name] = cluster
                else:
                    # Fallback to first business name
                    chain_name = cluster[0].get('name', normalized_name)
                    result_chains[chain_name] = cluster
            
            processed.add(normalized_name)
        
        return dict(result_chains)
    
    def _are_different_locations(self, group1: List[Dict], group2: List[Dict], min_distance_km: float = 0.5) -> bool:
        """
        Check if two groups of businesses are at different locations.
        
        Args:
            group1: First group of businesses
            group2: Second group of businesses
            min_distance_km: Minimum distance to consider locations different
            
        Returns:
            True if groups are at different locations
        """
        for b1 in group1:
            for b2 in group2:
                lat1 = b1.get('lat', 0)
                lon1 = b1.get('lon', 0)
                lat2 = b2.get('lat', 0)
                lon2 = b2.get('lon', 0)
                
                # Skip if coordinates are missing
                if not all([lat1, lon1, lat2, lon2]):
                    continue
                
                distance = self._calculate_distance(lat1, lon1, lat2, lon2)
                if distance >= min_distance_km:
                    return True
        return False
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def enrich_businesses_with_chain_data(self, businesses: List[Dict], business_type: str = "business") -> List[Dict]:
        """
        Enrich nearby businesses with city-wide chain information AND
        detect chains within the results themselves.
        
        Args:
            businesses: List of nearby businesses
            business_type: Type of business for context
            
        Returns:
            Enriched businesses with chain data
        """
        # First, detect chains within the current results
        result_chains = self.detect_chains_in_results(businesses)
        
        # Use LLM to classify businesses as branded or local
        llm_classified_businesses = self.llm_brand_detector.batch_identify_brands(businesses, business_type)
        
        enriched = []
        for business in llm_classified_businesses:
            business_copy = business.copy()
            
            # Check city-wide chain database
            chain_info = self.check_if_chain(business.get('name', ''))
            business_copy['city_chain_info'] = chain_info
            
            # Check if it's part of a chain detected in current results
            is_result_chain = False
            result_chain_info = None
            
            for chain_name, chain_locations in result_chains.items():
                # Check if this business is part of this chain
                for loc in chain_locations:
                    # Match by coordinates
                    if (abs(loc.get('lat', 0) - business.get('lat', 0)) < 0.0001 and
                        abs(loc.get('lon', 0) - business.get('lon', 0)) < 0.0001):
                        is_result_chain = True
                        result_chain_info = {
                            'is_result_chain': True,
                            'chain_name': chain_name,
                            'total_result_locations': len(chain_locations),
                            'description': f"Found {len(chain_locations)} locations of this business nearby"
                        }
                        break
                
                if is_result_chain:
                    break
            
            business_copy['result_chain_info'] = result_chain_info
            
            # Use LLM classification as primary source, fallback to rule-based detection
            is_branded = business.get('is_branded', False)
            brand_name = business.get('brand_name', business.get('name', ''))
            confidence = business.get('confidence', 0.5)
            
            # Mark as chain if either database, results, or LLM indicate it's a chain
            if (chain_info['is_local_chain'] or is_result_chain or is_branded):
                business_copy['is_local_chain'] = True
                business_copy['is_chain'] = True  # For compatibility with Streamlit app
                business_copy['local_chain_name'] = (
                    chain_info.get('chain_name') or 
                    (result_chain_info.get('chain_name') if result_chain_info else brand_name)
                )
                business_copy['total_locations'] = (
                    chain_info.get('total_locations', 1) +
                    (result_chain_info.get('total_result_locations', 0) if result_chain_info else 1)
                )
                business_copy['brand_classification_confidence'] = confidence
                business_copy['brand_classification_reasoning'] = business.get('reasoning', '')
            else:
                business_copy['is_local_chain'] = False
                business_copy['is_chain'] = False  # For compatibility with Streamlit app
                business_copy['local_chain_name'] = business.get('name', '')
                business_copy['total_locations'] = 1
                business_copy['brand_classification_confidence'] = confidence
                business_copy['brand_classification_reasoning'] = business.get('reasoning', '')
            
            enriched.append(business_copy)
        
        return enriched
    
    def _normalize_brand_name(self, name: str) -> str:
        """
        Normalize business name to detect chains.
        
        Examples:
            "Sharma Cafe - Sector 12" -> "sharma cafe"
            "Sharma Cafe, Phase 7" -> "sharma cafe"
            "Sharma's Cafe #3" -> "sharma cafe"
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove possessive apostrophes
        normalized = normalized.replace("'s", "").replace("'", "")
        
        # Remove location/branch indicators
        patterns = [
            r'\s*-\s*.*',  # Everything after dash
            r'\s*,\s*.*',  # Everything after comma
            r'\s*#\d+',    # Branch numbers (#1, #2)
            r'\s*\(.*\)',  # Content in parentheses
            r'\s+branch\s*\d*',
            r'\s+outlet\s*\d*',
            r'\s+store\s*\d*',
            r'\s+shop\s*\d*',
            r'\s+sector\s+\d+',
            r'\s+phase\s+\d+',
            r'\s+scf\s+\d+',
            r'\s+sco\s+\d+',
            r'\s+block\s+\w+',
            r'\s+mall.*',
            r'\s+market.*',
            r'\s+plaza.*',
            r'\s+complex.*'
        ]
        
        for pattern in patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Clean whitespace
        normalized = ' '.join(normalized.split()).strip()
        
        # Take first 2-3 meaningful words (core brand name)
        words = normalized.split()
        if len(words) > 3:
            normalized = ' '.join(words[:3])
        
        return normalized
    
    def get_chain_statistics(self) -> Dict[str, Any]:
        """Get statistics about chains in the city."""
        total_chains = len(self.chain_cache)
        
        # Count by location count
        location_distribution = defaultdict(int)
        for brand, locations in self.chain_cache.items():
            count = len(locations)
            location_distribution[count] += 1
        
        # Top chains by location count
        top_chains = sorted(
            self.chain_cache.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        return {
            'total_local_chains': total_chains,
            'location_distribution': dict(location_distribution),
            'top_chains': [
                {
                    'brand': brand.title(),
                    'locations': len(locations),
                    'sample_addresses': [loc['address'] for loc in locations[:3]]
                }
                for brand, locations in top_chains
            ]
        }