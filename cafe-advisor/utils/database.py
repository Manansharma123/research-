"""SQLite database utilities for storing reviews and nearby places data."""

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

# Database file paths
SERP_API_DB = "data/serp_api_data.db"
NEARBY_PLACES_DB = "data/nearby_places.db"

def init_databases():
    """Initialize both databases with required tables."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize SerpAPI database
        _init_serp_api_db()
        
        # Initialize nearby places database
        _init_nearby_places_db()
        
        logger.info("Databases initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing databases: {e}")
        raise


def _init_serp_api_db():
    """Initialize SerpAPI database with reviews table."""
    conn = sqlite3.connect(SERP_API_DB)
    cursor = conn.cursor()
    
    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            business_id TEXT,
            review_text TEXT,
            rating INTEGER,
            review_date TEXT,
            reviewer_name TEXT,
            latitude REAL,
            longitude REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(business_name, review_text)
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_location 
        ON reviews(latitude, longitude)
    """)
    
    # Create index for business_id for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_business_id 
        ON reviews(business_id)
    """)
    
    conn.commit()
    conn.close()


def _init_nearby_places_db():
    """Initialize nearby places database with places table."""
    conn = sqlite3.connect(NEARBY_PLACES_DB)
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            rating REAL,
            reviews_count INTEGER,
            place_type TEXT,
            business_id TEXT,
            latitude REAL,
            longitude REAL,
            price_level TEXT,
            vicinity TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, latitude, longitude)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_places_location 
        ON places(latitude, longitude)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_places_type 
        ON places(place_type)
    """)
    
    conn.commit()
    conn.close()


def store_serp_reviews(business_name: str, business_id: str, reviews: List[Dict], 
                      latitude: float, longitude: float):
    """
    Store SerpAPI reviews in the database.
    
    Args:
        business_name: Name of the business
        business_id: Business ID from SerpAPI
        reviews: List of review dictionaries
        latitude: Latitude of the business
        longitude: Longitude of the business
    """
    try:
        conn = sqlite3.connect(SERP_API_DB)
        cursor = conn.cursor()
        
        for review in reviews:
            cursor.execute("""
                INSERT OR IGNORE INTO reviews 
                (business_name, business_id, review_text, rating, review_date, reviewer_name, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                business_name,
                business_id,
                review.get("snippet", ""),
                review.get("rating", 0),
                review.get("date", ""),
                review.get("source", ""),
                latitude,
                longitude
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(reviews)} reviews for {business_name}")
    except Exception as e:
        logger.error(f"Error storing reviews for {business_name}: {e}")


def get_serp_reviews(latitude: float, longitude: float, radius: float = 3000, business_id: Optional[str] = None) -> List[Dict]:
    """
    Get SerpAPI reviews from the database within a radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius: Search radius in meters (default: 3000)
        business_id: Optional filter by business ID
        
    Returns:
        List of review dictionaries
    """
    try:
        conn = sqlite3.connect(SERP_API_DB)
        cursor = conn.cursor()
        
        # Build query with optional business_id filter
        if business_id:
            cursor.execute("""
                SELECT business_name, business_id, review_text, rating, review_date, reviewer_name, latitude, longitude
                FROM reviews 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
                AND business_id = ?
            """, (
                latitude - radius/111000,  # Approximate conversion
                latitude + radius/111000,
                longitude - radius/111000,
                longitude + radius/111000,
                business_id
            ))
        else:
            cursor.execute("""
                SELECT business_name, business_id, review_text, rating, review_date, reviewer_name, latitude, longitude
                FROM reviews 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
            """, (
                latitude - radius/111000,  # Approximate conversion
                latitude + radius/111000,
                longitude - radius/111000,
                longitude + radius/111000
            ))
        
        rows = cursor.fetchall()
        conn.close()
        
        reviews = []
        for row in rows:
            reviews.append({
                "business_name": row[0],
                "business_id": row[1],
                "snippet": row[2],
                "rating": row[3],
                "date": row[4],
                "source": row[5],
                "latitude": row[6],
                "longitude": row[7]
            })
        
        return reviews
    except Exception as e:
        logger.error(f"Error retrieving reviews: {e}")
        return []


def store_nearby_places(places: List[Dict], latitude: float, longitude: float):
    """
    Store nearby places in the database.
    
    Args:
        places: List of place dictionaries
        latitude: Latitude of the search center
        longitude: Longitude of the search center
    """
    try:
        conn = sqlite3.connect(NEARBY_PLACES_DB)
        cursor = conn.cursor()
        
        for place in places:
            cursor.execute("""
                INSERT OR IGNORE INTO places 
                (name, address, rating, reviews_count, place_type, business_id, latitude, longitude, price_level, vicinity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place.get("name", ""),
                place.get("address", ""),
                place.get("rating", 0),
                place.get("reviews_count", 0),
                place.get("type", ""),
                place.get("data_id", ""),
                place.get("latitude", 0),
                place.get("longitude", 0),
                place.get("price", ""),
                place.get("vicinity", "")
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(places)} nearby places")
    except Exception as e:
        logger.error(f"Error storing nearby places: {e}")


def get_nearby_places(latitude: float, longitude: float, radius: float = 3000, place_type: Optional[str] = None) -> List[Dict]:
    """
    Get nearby places from the database within a radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius: Search radius in meters (default: 3000)
        place_type: Optional filter by place type
        
    Returns:
        List of place dictionaries
    """
    try:
        conn = sqlite3.connect(NEARBY_PLACES_DB)
        cursor = conn.cursor()
        
        # Build query with optional place type filter
        if place_type:
            cursor.execute("""
                SELECT name, address, rating, reviews_count, place_type, business_id, latitude, longitude, price_level, vicinity
                FROM places 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
                AND place_type LIKE ?
            """, (
                latitude - radius/111000,
                latitude + radius/111000,
                longitude - radius/111000,
                longitude + radius/111000,
                f"%{place_type}%"
            ))
        else:
            cursor.execute("""
                SELECT name, address, rating, reviews_count, place_type, business_id, latitude, longitude, price_level, vicinity
                FROM places 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
            """, (
                latitude - radius/111000,
                latitude + radius/111000,
                longitude - radius/111000,
                longitude + radius/111000
            ))
        
        rows = cursor.fetchall()
        conn.close()
        
        places = []
        for row in rows:
            places.append({
                "name": row[0],
                "address": row[1],
                "rating": row[2],
                "reviews_count": row[3],
                "type": row[4],
                "data_id": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "price": row[8],
                "vicinity": row[9]
            })
        
        return places
    except Exception as e:
        logger.error(f"Error retrieving nearby places: {e}")
        return []


# Add this function after get_nearby_places()

def store_amenities(amenities: List[Dict], latitude: float, longitude: float):
    """
    Store amenities (hospitals, schools, universities) in the database.
    
    Args:
        amenities: List of amenity dictionaries
        latitude: Latitude of the search center
        longitude: Longitude of the search center
    """
    try:
        conn = sqlite3.connect(NEARBY_PLACES_DB)
        cursor = conn.cursor()
        
        for amenity in amenities:
            cursor.execute("""
                INSERT OR IGNORE INTO places
                (name, address, rating, reviews_count, place_type, business_id, 
                 latitude, longitude, price_level, vicinity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                amenity.get("name", ""),
                amenity.get("address", ""),
                amenity.get("rating", 0),
                amenity.get("reviews_count", 0),
                amenity.get("amenity_type", ""),  # Use amenity_type
                amenity.get("data_id", ""),
                amenity.get("latitude", latitude),
                amenity.get("longitude", longitude),
                amenity.get("price", ""),
                amenity.get("vicinity", "")
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(amenities)} amenities")
        
    except Exception as e:
        logger.error(f"Error storing amenities: {e}")


def get_amenities_by_type(latitude: float, longitude: float, 
                          amenity_types: List[str], 
                          radius: float = 5000) -> Dict[str, List[Dict]]:
    """
    Get amenities grouped by type from the database within a radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        amenity_types: List of amenity types to retrieve
        radius: Search radius in meters (default: 5000)
        
    Returns:
        Dictionary mapping amenity types to their lists of places
    """
    try:
        conn = sqlite3.connect(NEARBY_PLACES_DB)
        cursor = conn.cursor()
        
        results = {}
        
        for amenity_type in amenity_types:
            cursor.execute("""
                SELECT name, address, rating, reviews_count, place_type, business_id, 
                       latitude, longitude, price_level, vicinity
                FROM places
                WHERE latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                AND place_type = ?
                ORDER BY rating DESC
            """, (
                latitude - radius/111000,
                latitude + radius/111000,
                longitude - radius/111000,
                longitude + radius/111000,
                amenity_type
            ))
            
            rows = cursor.fetchall()
            
            places = []
            for row in rows:
                places.append({
                    "name": row[0],
                    "address": row[1],
                    "rating": row[2],
                    "reviews_count": row[3],
                    "amenity_type": row[4],
                    "data_id": row[5],
                    "latitude": row[6],
                    "longitude": row[7],
                    "price": row[8],
                    "vicinity": row[9]
                })
            
            results[amenity_type] = places
        
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving amenities: {e}")
        return {}


def clear_database(db_path: str):
    """
    Clear all data from a database.
    
    Args:
        db_path: Path to the database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Clear all tables
        for table in tables:
            cursor.execute(f"DELETE FROM {table[0]}")
        
        conn.commit()
        conn.close()
        logger.info(f"Cleared database: {db_path}")
    except Exception as e:
        logger.error(f"Error clearing database {db_path}: {e}")


def get_cached_business_ids(latitude: float, longitude: float, radius: float = 3000) -> List[str]:
    """
    Get list of cached business IDs from the database within a radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius: Search radius in meters (default: 3000)
        
    Returns:
        List of business IDs
    """
    try:
        conn = sqlite3.connect(NEARBY_PLACES_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT business_id
            FROM places 
            WHERE latitude BETWEEN ? AND ? 
            AND longitude BETWEEN ? AND ?
            AND business_id IS NOT NULL
        """, (
            latitude - radius/111000,
            latitude + radius/111000,
            longitude - radius/111000,
            longitude + radius/111000
        ))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        logger.error(f"Error retrieving cached business IDs: {e}")
        return []


def check_connection() -> bool:
    """
    Check if database connections are working.
    
    Returns:
        bool: True if connections work, False otherwise
    """
    try:
        # Test SerpAPI database
        conn1 = sqlite3.connect(SERP_API_DB)
        cursor1 = conn1.cursor()
        cursor1.execute("SELECT 1")
        conn1.close()
        
        # Test Nearby Places database
        conn2 = sqlite3.connect(NEARBY_PLACES_DB)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT 1")
        conn2.close()
        
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False
