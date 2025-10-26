import time
import sys
import re
import os
import json
import requests
from typing import List, Dict, Optional, Any
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Serper API Configuration
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
SERPER_API_URL = "https://google.serper.dev/search"

def make_driver(headless: bool = False) -> webdriver.Chrome:
    """Initialize Chrome WebDriver with optimal settings."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

def safe_find(el, by, value):
    """Safely find an element without throwing exceptions."""
    try:
        return el.find_element(by, value)
    except NoSuchElementException:
        return None

def safe_text(el) -> str:
    """Safely extract text from an element."""
    try:
        if el is None:
            return ""
        return el.text.strip()
    except Exception:
        return ""

def safe_get_attribute(el, attr: str) -> str:
    """Safely get attribute value from an element."""
    try:
        if el is None:
            return ""
        val = el.get_attribute(attr)
        return val.strip() if val else ""
    except Exception:
        return ""

def detect_query_intent(query: str) -> Dict[str, str]:
    """
    Detect user intent and map to appropriate platform.
    Returns: {platform, search_query, category}
    """
    query_lower = query.lower()
    
    # Platform mapping based on keywords
    # Note: Cafe/Restaurant queries are handled by swiggy_scraper.py
    platform_mapping = {
        # Hotels & Accommodation
        'hotel': {'platform': 'Booking.com', 'category': 'accommodation'},
        'resort': {'platform': 'Booking.com', 'category': 'accommodation'},
        'accommodation': {'platform': 'Booking.com', 'category': 'accommodation'},
        'stay': {'platform': 'Booking.com', 'category': 'accommodation'},
        'lodge': {'platform': 'Booking.com', 'category': 'accommodation'},
        
        # Shopping
        'shop': {'platform': 'Flipkart', 'category': 'shopping'},
        'shopping': {'platform': 'Flipkart', 'category': 'shopping'},
        'buy': {'platform': 'Flipkart', 'category': 'shopping'},
        'store': {'platform': 'Flipkart', 'category': 'shopping'},
        
        # Electronics
        'electronics': {'platform': 'Flipkart', 'category': 'electronics'},
        'mobile': {'platform': 'Flipkart', 'category': 'electronics'},
        'laptop': {'platform': 'Flipkart', 'category': 'electronics'},
        'phone': {'platform': 'Flipkart', 'category': 'electronics'},
        
        # Grocery
        'grocery': {'platform': 'BigBasket', 'category': 'grocery'},
        'vegetables': {'platform': 'BigBasket', 'category': 'grocery'},
        'fruits': {'platform': 'BigBasket', 'category': 'grocery'},
        
        # Gym & Fitness
        'gym': {'platform': 'Cult.fit', 'category': 'fitness'},
        'fitness': {'platform': 'Cult.fit', 'category': 'fitness'},
        'workout': {'platform': 'Cult.fit', 'category': 'fitness'},
    }
    
    # Detect platform based on keywords
    detected_platform = None
    detected_category = 'general'
    
    for keyword, info in platform_mapping.items():
        if keyword in query_lower:
            detected_platform = info['platform']
            detected_category = info['category']
            break
    
    # If no specific platform detected, use general search
    if not detected_platform:
        detected_platform = 'General'
    
    return {
        'platform': detected_platform,
        'category': detected_category,
        'original_query': query
    }

def search_business_with_serper(business_name: str) -> Optional[str]:
    """
    Use Serper API to search for a business and return its URL.
    Intelligently detects user intent and searches appropriate platform.
    """
    if not SERPER_API_KEY:
        print("⚠️  SERPER_API_KEY not found in environment variables.")
        print("Please set it: export SERPER_API_KEY='your_api_key'")
        return None
    
    # Detect user intent
    intent = detect_query_intent(business_name)
    platform = intent['platform']
    category = intent['category']
    
    # Build smart search query
    if platform != 'General':
        if platform == 'Booking.com':
            # Preserve full location details for hotels
            search_query = f"Booking.com {business_name} (in India)"
        else:
            search_query = f"{platform} {business_name} (in India)"
        print(f"🎯 Detected: {category.upper()} query")
        print(f"🔍 Searching on: {platform}")
    else:
        search_query = f"{business_name} (in India)"
        print(f"🔍 Searching for: {business_name}")
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'q': search_query,
        'num': 10,
        'gl': 'in',  # Set country to India
        'hl': 'en'   # Language: English
    }
    
    try:
        print(f"🌐 Query: {search_query}")
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organic results
        organic_results = data.get('organic', [])
        
        if not organic_results:
            print("❌ No results found.")
            return None
        
        # Automatically select the first (best) result
        selected_url = organic_results[0].get('link')
        selected_title = organic_results[0].get('title', 'N/A')
        
        print(f"\n✅ Found and selected: {selected_title}")
        print(f"🔗 URL: {selected_url}\n")
        
        return selected_url
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Serper API: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def detect_card_elements(driver) -> List[Any]:
    """
    Dynamically detect card-like elements on the page.
    Tries multiple common patterns used for product/service cards.
    """
    card_selectors = [
        # Common card patterns
        "div[class*='card']",
        "div[class*='Card']",
        "div[class*='item']",
        "div[class*='Item']",
        "div[class*='product']",
        "div[class*='Product']",
        "article",
        "div[class*='listing']",
        "div[class*='result']",
        "li[class*='item']",
        "div[data-testid*='card']",
        "div[data-testid*='item']",
        "div[data-testid*='product']",
        "div[class*='box']",
        "div[class*='tile']",
    ]
    
    all_cards = []
    for selector in card_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            # Filter elements that have reasonable size and content
            for elem in elements:
                try:
                    if elem.is_displayed() and len(safe_text(elem)) > 20:
                        all_cards.append(elem)
                except:
                    continue
        except:
            continue
    
    # Remove duplicates (keep unique elements)
    unique_cards = []
    seen_texts = set()
    for card in all_cards:
        text = safe_text(card)[:100]  # First 100 chars as fingerprint
        if text and text not in seen_texts:
            seen_texts.add(text)
            unique_cards.append(card)
    
    return unique_cards

def _get_scroll_height(driver) -> int:
    """Get current scroll height of the page."""
    try:
        return int(driver.execute_script("return document.body.scrollHeight || document.documentElement.scrollHeight || 0;"))
    except Exception:
        return 0

def _find_show_more(driver, timeout=6):
    """Find 'Show More' or 'Load More' buttons."""
    xpath = ("((//button | //div)[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show more') or "
             "contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'load more')])[last()]")
    try:
        return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        return None

def scroll_and_load_content(driver, max_scrolls: int = 10):
    """
    Scroll the page to load dynamic content and click 'Show More' buttons.
    """
    print("\n📜 Scrolling to load all content...")
    
    last_height = _get_scroll_height(driver)
    scrolls = 0
    
    while scrolls < max_scrolls:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Try to click 'Show More' or 'Load More' buttons
        btn = _find_show_more(driver, timeout=2)
        if btn:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)
                print("  ✓ Clicked 'Show More' button")
                time.sleep(2)
            except:
                pass
        
        # Check if height changed
        new_height = _get_scroll_height(driver)
        if new_height == last_height:
            scrolls += 1
        else:
            scrolls = 0
            last_height = new_height
    
    print("✅ Finished loading content\n")

def extract_booking_com_card_data(card) -> Dict:
    """
    Extract data specifically from Booking.com hotel cards.
    Extracts: name, price, rating, description, amenities, etc.
    """
    data = {
        "name": "",
        "price": "",
        "rating": "",
        "description": "",
        "location": "",
        "amenities": "",
        "link": "",
        "image": ""
    }
    
    card_text = safe_text(card)
    
    # Skip if this looks like a filter or navigation element
    if "Filter by" in card_text or len(card_text) < 20:
        return data
    
    # Extract hotel name - try multiple approaches
    name_el = safe_find(card, By.XPATH, ".//div[@data-testid='title']")
    if not name_el:
        name_el = safe_find(card, By.XPATH, ".//h3 | .//h2 | .//h4")
    if not name_el:
        # Look for any bold/strong text at the beginning
        name_el = safe_find(card, By.XPATH, ".//strong | .//b")
    
    if name_el:
        name_text = safe_text(name_el)
        # Clean up "Hotel in City" suffix
        name_text = re.sub(r'\s+Hotel in \w+$', '', name_text)
        if name_text and len(name_text) > 2:
            data["name"] = name_text
    
    # If still no name, use first line of card text
    if not data["name"]:
        lines = [l.strip() for l in card_text.split('\n') if l.strip() and len(l.strip()) > 5]
        if lines:
            data["name"] = lines[0][:100]
    
    # Extract price - multiple patterns with improved approach
    price_patterns = [
        r'₹\s*([\d,]+(?:\.\d+)?)',
        r'Price\s*₹\s*([\d,]+(?:\.\d+)?)',
        r'₹([\d,]+)',
        r'Rs\.\s*([\d,]+)'
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, card_text)
        if price_match:
            data["price"] = "₹" + price_match.group(1)
            break
    
    # Extract rating - look for patterns like "9.1", "8.5", "Scored 9.1"
    rating_patterns = [
        r'Scored\s+(\d+\.?\d*)',
        r'(\d+\.\d+)\s+(?:Superb|Excellent|Very Good|Good|Fabulous|Exceptional)',
        r'rating\s+(\d+\.?\d*)',
        r'\b(\d+\.\d+)\s+out of',
        r'(\d+\.\d+)\s*/\s*10',
        r'(\d+\.\d+)'
    ]
    
    for pattern in rating_patterns:
        rating_match = re.search(pattern, card_text, re.IGNORECASE)
        if rating_match:
            rating_val = rating_match.group(1)
            try:
                rating_num = float(rating_val)
                # Handle different rating scales
                if 0 <= rating_num <= 5:  # 5-point scale
                    data["rating"] = str(rating_num)
                    break
                elif 0 <= rating_num <= 10:  # 10-point scale
                    data["rating"] = str(rating_num / 2)  # Convert to 5-point scale
                    break
            except:
                pass
    
    # Extract description - look for descriptive text
    # Usually contains words like "offering", "featuring", "located", etc.
    desc_patterns = [
        r'((?:Offering|Featuring|Located|Set|Situated|Built|Boasting)[^\.]+\.)',
        r'((?:This|The)\s+(?:hotel|property|accommodation)[^\.]+\.)',
        r'([^\.]{50,200}hotel[^\.]*\.)'
    ]
    
    for pattern in desc_patterns:
        desc_match = re.search(pattern, card_text, re.IGNORECASE)
        if desc_match:
            data["description"] = desc_match.group(1)[:300]
            break
    
    # If no description found, extract amenities-like text
    if not data["description"]:
        # Look for amenity keywords
        amenity_keywords = ['pool', 'spa', 'wifi', 'parking', 'restaurant', 'gym', 'fitness', 'breakfast', 'room service', 'ac', 'air conditioning']
        desc_parts = []
        for keyword in amenity_keywords:
            if keyword.lower() in card_text.lower():
                desc_parts.append(keyword.title())
        if desc_parts:
            data["description"] = "Features: " + ", ".join(desc_parts[:5])
    
    # Extract amenities from card text with improved approach
    amenities = []
    
    # Look for specific amenity elements
    try:
        amenity_elements = card.find_elements(By.XPATH, ".//*[contains(@data-testid, 'facility') or contains(@class, 'facility') or contains(text(), 'Free') or contains(text(), 'facility')]")
        for el in amenity_elements:
            amenity_text = safe_text(el)
            if amenity_text and len(amenity_text) > 2:
                amenities.append(amenity_text)
    except:
        pass
    
    # Also look for amenities in the text with specific patterns
    amenity_patterns = [
        r'Free\s+WiFi',
        r'Free\s+parking',
        r'Swimming\s+pool',
        r'Spa',
        r'Fitness\s+centre',
        r'Restaurant',
        r'Bar',
        r'Room\s+service',
        r'Air\s+conditioning',
        r'Breakfast',
        r'Free\s+breakfast',
        r'Wi-Fi',
        r'Gym',
        r'Parking',
        r'Internet'
    ]
    
    for pattern in amenity_patterns:
        if re.search(pattern, card_text, re.IGNORECASE):
            # Clean up the pattern for display
            clean_pattern = re.sub(r'\\s\+', ' ', pattern)
            clean_pattern = re.sub(r'\\', '', clean_pattern)
            amenities.append(clean_pattern)
    
    if amenities:
        # Remove duplicates and limit to 10 amenities
        unique_amenities = list(set(amenities))[:10]
        data["amenities"] = ", ".join(unique_amenities)
    
    # Extract location - look for area names with improved approach
    location_patterns = [
        r'(?:in|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*India',
        r'Location:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, card_text)
        if location_match:
            data["location"] = location_match.group(1)
            break
    
    # If still no location, try to find it in specific elements
    if not data["location"]:
        try:
            location_elements = card.find_elements(By.XPATH, ".//*[contains(text(), 'Location') or contains(text(), 'location') or contains(text(), 'Address')]")
            for el in location_elements:
                text = safe_text(el)
                # Look for city names in the text
                city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
                if city_match:
                    data["location"] = city_match.group(1)
                    break
        except:
            pass
    
    # Extract link with improved approach
    link_elem = safe_find(card, By.TAG_NAME, 'a')
    if link_elem:
        href = safe_get_attribute(link_elem, 'href')
        if href and 'booking.com/hotel' in href:
            data["link"] = href
    else:
        # Try to find any link in the card
        try:
            links = card.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = safe_get_attribute(link, 'href')
                if href and 'booking.com' in href and 'hotel' in href:
                    data["link"] = href
                    break
        except:
            pass
    
    # Extract image with improved approach
    img_elem = safe_find(card, By.TAG_NAME, 'img')
    if img_elem:
        src = safe_get_attribute(img_elem, 'src')
        if not src:
            src = safe_get_attribute(img_elem, 'data-src')
        if src and ('http' in src) and ('bstatic.com' in src or 'booking.com' in src):
            data["image"] = src
    else:
        # Try to find any image in the card
        try:
            images = card.find_elements(By.TAG_NAME, 'img')
            for img in images:
                src = safe_get_attribute(img, 'src')
                if not src:
                    src = safe_get_attribute(img, 'data-src')
                if src and 'http' in src and ('bstatic.com' in src or 'booking.com' in src):
                    data["image"] = src
                    break
        except:
            pass
    
    # Clean up all fields
    for k, v in list(data.items()):
        if isinstance(v, str):
            data[k] = v.replace("\n", " ").replace("  ", " ").strip()
    
    return data

def extract_universal_card_data(card) -> Dict:
    """
    Universal card data extraction that works for any website.
    Detects: name/title, price, rating, description, and other metadata.
    """
    data = {
        "name": "",
        "price": "",
        "rating": "",
        "description": "",
        "link": "",
        "image": "",
        "additional_info": ""
    }
    
    card_text = safe_text(card)
    
    # Extract Name/Title (look for headings)
    for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        heading = safe_find(card, By.TAG_NAME, tag)
        if heading:
            text = safe_text(heading)
            if text and len(text) > 2:
                data["name"] = text
                break
    
    # If no heading, look for strong/bold text or first meaningful line
    if not data["name"]:
        strong = safe_find(card, By.TAG_NAME, 'strong')
        if strong:
            data["name"] = safe_text(strong)
    
    if not data["name"]:
        # Try data-testid or aria-label attributes
        for attr in ['aria-label', 'title', 'data-title', 'data-name']:
            val = safe_get_attribute(card, attr)
            if val and len(val) > 2:
                data["name"] = val
                break
    
    # Extract Price (look for currency symbols and numbers)
    price_patterns = [
        r'[$₹€£¥]\s*[\d,]+(?:\.\d{2})?',
        r'[\d,]+(?:\.\d{2})?\s*[$₹€£¥]',
        r'(?:Rs\.?|INR|USD|EUR)\s*[\d,]+(?:\.\d{2})?',
        r'[\d,]+(?:\.\d{2})?\s*(?:Rs\.?|INR|USD|EUR)',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, card_text, re.IGNORECASE)
        if matches:
            data["price"] = matches[0]
            break
    
    # Extract Rating (look for star ratings or numeric ratings)
    rating_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:stars?|★|⭐)',
        r'(?:rating|rated)\s*:?\s*(\d+(?:\.\d+)?)',
        r'(\d+\.\d+)\s*/\s*5',
        r'^(\d+\.\d+)',
    ]
    
    # Try to find rating in text
    for pattern in rating_patterns:
        matches = re.findall(pattern, card_text, re.IGNORECASE)
        if matches:
            rating_val = matches[0] if isinstance(matches[0], str) else matches[0][0]
            try:
                rating_num = float(rating_val)
                if 0 <= rating_num <= 5:
                    data["rating"] = rating_val
                    break
            except:
                pass
    
    # Look for rating in specific elements
    if not data["rating"]:
        rating_selectors = [
            "*[class*='rating']",
            "*[class*='Rating']",
            "*[class*='star']",
            "*[class*='Star']",
            "*[data-testid*='rating']",
        ]
        for selector in rating_selectors:
            elem = safe_find(card, By.CSS_SELECTOR, selector)
            if elem:
                text = safe_text(elem)
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                if match:
                    data["rating"] = match.group(1)
                    break
    
    # Extract Link
    link_elem = safe_find(card, By.TAG_NAME, 'a')
    if link_elem:
        href = safe_get_attribute(link_elem, 'href')
        if href:
            data["link"] = href
    
    # Extract Image
    img_elem = safe_find(card, By.TAG_NAME, 'img')
    if img_elem:
        src = safe_get_attribute(img_elem, 'src')
        if not src:
            src = safe_get_attribute(img_elem, 'data-src')
        if src:
            data["image"] = src
    
    # Extract Description (look for paragraph or description text)
    desc_elem = safe_find(card, By.TAG_NAME, 'p')
    if desc_elem:
        desc_text = safe_text(desc_elem)
        if desc_text and len(desc_text) > 10:
            data["description"] = desc_text[:200]  # Limit to 200 chars
    
    # If no name found, use first line of card text
    if not data["name"]:
        lines = [ln.strip() for ln in card_text.split("\n") if ln.strip()]
        if lines:
            data["name"] = lines[0][:100]
    
    # Additional info (remaining text)
    if card_text:
        # Remove name, price, rating from additional info
        additional = card_text
        for val in [data["name"], data["price"], data["rating"]]:
            if val:
                additional = additional.replace(val, "")
        data["additional_info"] = " ".join(additional.split())[:300]
    
    # Clean up all fields
    for k, v in list(data.items()):
        if isinstance(v, str):
            data[k] = v.replace("\n", " ").strip()
    
    return data

def scrape_universal_cards(driver, url: str = "") -> List[Dict]:
    """
    Universal card scraping that works for any website.
    Detects if it's Booking.com and uses specialized extraction, otherwise uses generic extraction.
    Note: Cafe/Restaurant (Swiggy/Zomato) scraping is now handled by swiggy_scraper.py
    """
    # Check platform
    is_booking = "booking.com" in url.lower()
    
    print("\n🔍 Detecting card elements on the page...")
    
    # Initialize cards variable
    cards = []
    
    if is_booking:
        print("🏨 Detected Booking.com - Using specialized extraction")
        # Look for Booking.com hotel cards - try multiple selectors
        cards = driver.find_elements(By.XPATH, "//div[@data-testid='property-card']")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid*='property']")
        if not cards:
            # Look for cards with hotel images and prices
            cards = driver.find_elements(By.XPATH, "//div[.//img and contains(., '₹')]")
        
        # Filter out navigation/filter elements
        if cards:
            filtered_cards = []
            for card in cards:
                text = safe_text(card)
                # Skip if it's a filter, navigation, or too short
                if "Filter by" not in text and "Show on map" not in text and len(text) > 50:
                    filtered_cards.append(card)
            cards = filtered_cards[:50]  # Limit to 50 hotels
    else:
        cards = detect_card_elements(driver)
    
    if not cards:
        print("⚠️  No card elements detected. Trying alternative approach...")
        # Fallback: scrape all visible divs with substantial content
        cards = driver.find_elements(By.TAG_NAME, 'div')
        cards = [c for c in cards if len(safe_text(c)) > 100 and len(safe_text(c)) < 1500]
        cards = cards[:50]  # Limit fallback to 50
    
    print(f"📦 Found {len(cards)} potential card elements\n")
    
    seen, rows = set(), []
    print("🔄 Extracting data from cards...\n")
    
    for idx, card in enumerate(cards[:100], 1):  # Limit to first 100 cards
        try:
            # Use appropriate extraction method
            if is_booking:
                row = extract_booking_com_card_data(card)
                # Skip if no meaningful data
                if not row.get("name") or len(row.get("name", "")) < 2:
                    continue
                # Deduplication for Booking
                key = (row.get("name", ""), row.get("price", ""), row.get("location", ""))
            else:
                row = extract_universal_card_data(card)
                # Skip if no meaningful data
                if not row.get("name") or len(row.get("name", "")) < 2:
                    continue
                # Deduplication for general
                key = (row.get("name", ""), row.get("price", ""), row.get("rating", ""))
            
            if key in seen:
                continue
            seen.add(key)
            
            rows.append(row)
            
            # Print progress
            if is_booking:
                name = row.get('name', 'N/A')[:50]
                price = row.get('price', 'N/A')
                rating = row.get('rating', 'N/A')
                desc = row.get('description', 'N/A')[:40]
                print(f"✅ [{len(rows)}] {name}  |  {price}  |  ⭐ {rating}  |  {desc}")
            else:
                name = row.get('name', 'N/A')[:50]
                price = row.get('price', 'N/A')
                rating = row.get('rating', 'N/A')
                print(f"✅ [{len(rows)}] {name}  |  Price: {price}  |  Rating: {rating}")
            
        except StaleElementReferenceException:
            continue
        except Exception as e:
            continue
    
    print(f"\n📊 Total items scraped: {len(rows)}\n")
    return rows

def save_to_csv(rows: List[Dict], business_name: str = "scraped_data"):
    """Save scraped data to CSV file."""
    if not rows:
        print("❌ No results found to save.")
        return
    
    df = pd.DataFrame(rows)
    
    # Reorder columns for better readability
    # Check platform type based on columns
    if "location" in df.columns and "amenities" in df.columns:
        # Booking.com columns
        cols = ["name", "price", "rating", "description", "location", "amenities", "link", "image"]
        df = df[[c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]]
    else:
        # General columns
        cols = ["name", "price", "rating", "description", "link", "image", "additional_info"]
        df = df[[c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]]
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_business_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_')
    filename = f"scraped_{safe_business_name}_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"💾 Saved {len(df)} rows to {filename}")

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("🌐 UNIVERSAL WEB SCRAPER")
    print("="*80 + "\n")
    
    # Get business name from command line or user input
    business_name = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not business_name:
        business_name = input("Enter business name to search (e.g., 'IKEA furniture store'): ").strip()
    
    if not business_name:
        print("❌ No business name provided. Exiting.")
        return
    
    # Search for business URL using Serper API
    url = search_business_with_serper(business_name)
    
    if not url:
        print("❌ Could not find URL. Exiting.")
        return
    
    # Initialize WebDriver
    print("\n🚀 Launching browser...")
    driver = make_driver(headless=True)
    
    try:
        # Navigate to the URL
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Scroll and load all content (reduced scrolls for faster scraping)
        scroll_and_load_content(driver, max_scrolls=5)
        
        # Scrape the cards (pass URL for platform detection)
        rows = scrape_universal_cards(driver, url)
        
        # Save to CSV
        save_to_csv(rows, business_name)
        
        print("\n✅ Scraping completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
    finally:
        try:
            driver.quit()
            print("🔒 Browser closed.")
        except Exception:
            pass

if __name__ == "__main__":
    main()