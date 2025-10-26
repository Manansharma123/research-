"""Scraper node for extracting business data from web sources."""

import logging
import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.state import BusinessAnalysisState

logger = logging.getLogger(__name__)


def scraper_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to scrape business data based on extracted filters.
    This is an OPTIONAL enhancement - workflow continues even if scraping fails.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with scraped data (or empty list if scraping fails)
    """
    logger.info("Starting scraper node (optional enhancement)")
    
    try:
        # Extract filters from state
        extracted_filters = state.get("extracted_filters", {})
        
        # Debug logging
        logger.info(f"State keys: {list(state.keys())}")
        logger.info(f"Extracted filters: {extracted_filters}")
        
        primary_business = extracted_filters.get("primary_business", "")
        location = extracted_filters.get("location", "")
        coordinates = extracted_filters.get("coordinates", {})
        latitude = coordinates.get("latitude") if coordinates else state.get("latitude")
        longitude = coordinates.get("longitude") if coordinates else state.get("longitude")
        
        logger.info(f"Primary business: '{primary_business}', Location: '{location}', Coords: ({latitude}, {longitude})")
        
        if not primary_business or not location:
            logger.warning(f"Missing business type or location - skipping scraper")
            logger.warning(f"  primary_business: '{primary_business}'")
            logger.warning(f"  location: '{location}'")
            return {
                **state,
                "scraped_data": [],
                "scraper_executed": False,
                "current_step": "scraper_skipped"
            }
        
        # Check if scraper should run for this business type
        scraper_categories = ['cafe', 'restaurant', 'hotel', 'school']
        should_scrape = any(cat in primary_business.lower() for cat in scraper_categories)
        
        if not should_scrape:
            logger.info(f"Scraper not required for business type: {primary_business}")
            return {
                **state,
                "scraped_data": [],
                "scraper_executed": False,
                "current_step": "scraper_skipped"
            }
        
        logger.info(f"🔍 Scraping MANDATORY for: {primary_business} in {location}")
        
        # Determine which scraper to use
        scraped_data = []
        
        if "school" in primary_business.lower():
            # Use school scraper
            logger.info("Using school scraper...")
            try:
                scraped_data = run_school_scraper(location, latitude, longitude)
            except Exception as e:
                logger.error(f"School scraper failed: {e}")
                scraped_data = []
        elif any(cat in primary_business.lower() for cat in ['cafe', 'restaurant']):
            # Use Swiggy/Zomato scraper for cafe and restaurant
            logger.info(f"Using Swiggy/Zomato scraper for {primary_business}...")
            try:
                scraped_data = run_swiggy_scraper(primary_business, location, latitude, longitude)
            except Exception as e:
                logger.error(f"Swiggy/Zomato scraper failed: {e}")
                scraped_data = []
        else:
            # Use universal scraper for other businesses (hotel, etc.)
            logger.info(f"Using universal scraper for {primary_business}...")
            try:
                scraped_data = run_universal_scraper(primary_business, location, latitude, longitude)
            except Exception as e:
                logger.error(f"Universal scraper failed: {e}")
                scraped_data = []
        
        logger.info(f"Scraped {len(scraped_data)} items")
        
        # Always return success - empty list is acceptable
        return {
            **state,
            "scraped_data": scraped_data,
            "scraper_executed": True,
            "current_step": "scraper_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in scraper node: {str(e)}"
        logger.error(error_msg)
        # Don't fail the workflow - return empty scraped data
        logger.info("Continuing workflow without scraped data")
        return {
            **state,
            "scraped_data": [],
            "scraper_executed": False,
            "current_step": "scraper_completed"  # Still mark as completed
        }


def run_school_scraper(location: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """
    Run school scraper for the given location using Edustoke web scraping.
    
    Args:
        location: Location to search for schools
        latitude: Latitude coordinate (not used for Edustoke)
        longitude: Longitude coordinate (not used for Edustoke)
        
    Returns:
        List of scraped school data
    """
    try:
        # Import school scraper
        agents_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scraper_path = os.path.join(agents_dir, "scrapper.py", "school_scrapper.py")
        
        logger.info(f"🏫 Using Edustoke school scraper at: {scraper_path}")
        
        if not os.path.exists(scraper_path):
            logger.warning(f"School scraper not found at {scraper_path}")
            return []
        
        # Import the school scraper module
        import importlib.util
        spec = importlib.util.spec_from_file_location("school_scrapper", scraper_path)
        school_scrapper = importlib.util.module_from_spec(spec)
        sys.modules['school_scrapper'] = school_scrapper
        spec.loader.exec_module(school_scrapper)
        
        logger.info("✅ School scraper module loaded")
        
        # Setup driver
        driver = school_scrapper.setup_driver(headless=True)
        
        try:
            # Search for schools on Edustoke
            logger.info(f"🔍 Searching Edustoke for schools in: {location}")
            if school_scrapper.search_edustoke(driver, location, "Day School"):
                # Scroll and load content
                school_scrapper.scroll_and_load(driver, max_scrolls=10)
                
                # Scrape schools
                schools = school_scrapper.scrape_schools(driver)
                
                logger.info(f"✅ Scraped {len(schools)} schools from Edustoke")
                return schools
            else:
                logger.warning("School search failed on Edustoke")
                return []
                
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ Error running school scraper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def run_swiggy_scraper(business_name: str, location: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """
    Run Swiggy scraper for cafe and restaurant queries.
    
    Args:
        business_name: Type of business to search (cafe, restaurant)
        location: Location to search in
        latitude: Latitude coordinate (not used)
        longitude: Longitude coordinate (not used)
        
    Returns:
        List of scraped restaurant/cafe data
    """
    try:
        # Import swiggy scraper
        agents_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scraper_path = os.path.join(agents_dir, "scrapper.py", "swiggy_scraper.py")
        
        logger.info(f"🍽️ Using Swiggy scraper at: {scraper_path}")
        
        if not os.path.exists(scraper_path):
            logger.warning(f"Swiggy scraper not found at {scraper_path}")
            return []
        
        # Import the swiggy scraper module
        import importlib.util
        spec = importlib.util.spec_from_file_location("swiggy_scraper", scraper_path)
        swiggy_scraper = importlib.util.module_from_spec(spec)
        sys.modules['swiggy_scraper'] = swiggy_scraper
        spec.loader.exec_module(swiggy_scraper)
        
        logger.info("✅ Swiggy scraper module loaded")
        
        # Use the scrape_swiggy function from swiggy_scraper
        search_query = f"{business_name} near {location}"
        logger.info(f"🔍 Scraping: {search_query}")
        
        # Call the main scraping function
        scraped_data = swiggy_scraper.scrape_swiggy(business_name, location, max_results=50)
        
        logger.info(f"✅ Scraped {len(scraped_data)} items from Swiggy")
        return scraped_data
            
    except Exception as e:
        logger.error(f"❌ Error running Swiggy scraper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def run_universal_scraper(business_name: str, location: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """
    Run universal scraper for the given business and location using web scraping.
    Handles hotels and other businesses (NOT cafe/restaurant - those use swiggy_scraper.py).
    
    Args:
        business_name: Type of business to search (hotel, etc.)
        location: Location to search in
        latitude: Latitude coordinate (not used)
        longitude: Longitude coordinate (not used)
        
    Returns:
        List of scraped business data
    """
    try:
        # Import universal scraper
        agents_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scraper_path = os.path.join(agents_dir, "scrapper.py", "universal_scrapper.py")
        
        logger.info(f"🌐 Using universal web scraper at: {scraper_path}")
        
        if not os.path.exists(scraper_path):
            logger.warning(f"Universal scraper not found at {scraper_path}")
            return []
        
        # Import the universal scraper module
        import importlib.util
        spec = importlib.util.spec_from_file_location("universal_scrapper", scraper_path)
        universal_scrapper = importlib.util.module_from_spec(spec)
        sys.modules['universal_scrapper'] = universal_scrapper
        spec.loader.exec_module(universal_scrapper)
        
        logger.info("✅ Universal scraper module loaded")
        
        # Combine business and location for search query
        search_query = f"{business_name} near {location}"
        
        logger.info(f"🔍 Searching for: {search_query}")
        
        # Search for business URL using Serper API
        url = universal_scrapper.search_business_with_serper(search_query)
        
        if not url:
            logger.warning("Could not find URL for business")
            return []
        
        logger.info(f"✅ Found URL: {url}")
        
        # Setup driver
        driver = universal_scrapper.make_driver(headless=True)
        
        try:
            # Navigate to URL
            logger.info(f"🌐 Navigating to: {url}")
            driver.get(url)
            
            import time
            time.sleep(5)  # Wait for page to load
            
            # Scroll and load content
            universal_scrapper.scroll_and_load_content(driver, max_scrolls=5)
            
            # Scrape the data
            scraped_data = universal_scrapper.scrape_universal_cards(driver, url)
            
            logger.info(f"✅ Scraped {len(scraped_data)} items")
            return scraped_data
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ Error running universal scraper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
