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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

# Load environment variables
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


def extract_location_from_query(query: str) -> dict:
    """
    Extract location from user query.
    Examples:
        - "cafe near Noble Aurellia" -> {"location": "Noble Aurellia", "search_term": "cafe"}
        - "restaurants in Vijay Nagar" -> {"location": "Vijay Nagar", "search_term": "restaurants"}
    """
    query_lower = query.lower()
    
    # Patterns to extract location
    location_patterns = [
        r'(?:near|at|in)\s+(.+?)(?:\s+indore|\s+chandigarh|\s+delhi|$)',
        r'(?:near|at|in)\s+(.+)',
    ]
    
    location = None
    for pattern in location_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break
    
    # Extract search term (cafe, restaurant, etc.)
    search_terms = ['cafe', 'restaurant', 'food', 'dine', 'dining', 'eatery', 'bistro']
    search_term = None
    for term in search_terms:
        if term in query_lower:
            search_term = term
            break
    
    if not search_term:
        search_term = "restaurant"
    
    return {
        "location": location,
        "search_term": search_term,
        "original_query": query
    }


def detect_query_intent(query: str) -> Dict[str, str]:
    """
    Detect user intent and map to appropriate platform.
    Returns: {platform, search_query, category}
    """
    query_lower = query.lower()
    
    # Platform mapping based on keywords
    platform_mapping = {
        'cafe': {'platform': 'Swiggy Dineout', 'category': 'dining'},
        'restaurant': {'platform': 'Swiggy Dineout', 'category': 'dining'},
        'food': {'platform': 'Swiggy', 'category': 'food'},
        'dine': {'platform': 'Swiggy Dineout', 'category': 'dining'},
        'dining': {'platform': 'Swiggy Dineout', 'category': 'dining'},
    }
    
    detected_platform = None
    detected_category = 'general'
    
    for keyword, info in platform_mapping.items():
        if keyword in query_lower:
            detected_platform = info['platform']
            detected_category = info['category']
            break
    
    if not detected_platform:
        detected_platform = 'Swiggy Dineout'
    
    return {
        'platform': detected_platform,
        'category': detected_category,
        'original_query': query
    }


def search_business_with_serper(business_name: str) -> Optional[str]:
    """
    Use Serper API to search for a business and return its URL.
    """
    if not SERPER_API_KEY:
        print("⚠ SERPER_API_KEY not found. Using manual platform selection.")
        return None
    
    intent = detect_query_intent(business_name)
    platform = intent['platform']
    
    if platform == 'Swiggy Dineout':
        search_query = f"Swiggy Dineout {business_name} (in India)"
    else:
        search_query = f"{platform} {business_name} (in India)"
    
    print(f"🎯 Detected: {intent['category'].upper()} query")
    print(f"🔍 Searching on: {platform}")
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'q': search_query,
        'num': 10,
        'gl': 'in',
        'hl': 'en'
    }
    
    try:
        print(f"🌐 Query: {search_query}")
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        organic_results = data.get('organic', [])
        if not organic_results:
            print("❌ No results found.")
            return None
        
        selected_url = organic_results[0].get('link')
        selected_title = organic_results[0].get('title', 'N/A')
        
        print(f"\n✅ Found: {selected_title}")
        print(f"🔗 URL: {selected_url}\n")
        
        return selected_url
        
    except Exception as e:
        print(f"❌ Error calling Serper API: {e}")
        return None


def scroll_and_load_content(driver, max_scrolls: int = 10):
    """Scroll the page to load dynamic content."""
    print("\n📜 Scrolling to load all content...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scrolls += 1
        else:
            scrolls = 0
            last_height = new_height
    
    print("✅ Finished loading content\n")


def detect_card_elements(driver) -> List[Any]:
    """Dynamically detect card-like elements on the page."""
    card_selectors = [
        "div[class*='card']",
        "div[class*='Card']",
        "div[class*='item']",
        "article",
        "div[class*='listing']",
    ]
    
    all_cards = []
    for selector in card_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    if elem.is_displayed() and len(safe_text(elem)) > 20:
                        all_cards.append(elem)
                except:
                    continue
        except:
            continue
    
    # Remove duplicates
    unique_cards = []
    seen_texts = set()
    for card in all_cards:
        text = safe_text(card)[:100]
        if text and text not in seen_texts:
            seen_texts.add(text)
            unique_cards.append(card)
    
    return unique_cards


def set_location_on_swiggy(driver, location: str, max_retries: int = 3) -> bool:
    """Automatically set location on Swiggy Dineout with improved button clicking."""
    print(f"\n📍 Setting location on Swiggy to: {location}")
    
    for attempt in range(max_retries):
        try:
            print(f"\n🔄 Attempt {attempt + 1}/{max_retries}")
            time.sleep(2)
            
            # Step 1: Find and click "Setup your precise location" button
            print(" 🔍 Looking for 'Setup your precise location' button...")
            
            location_button_selectors = [
                # Text-based selectors
                "//div[contains(text(), 'Setup your precise location')]",
                "//button[contains(text(), 'Setup your precise location')]",
                "//div[contains(., 'Setup your precise location')]",
                "//*[contains(text(), 'Setup your precise location')]",
                
                # Class-based selectors from the screenshot
                "//div[contains(@class, 'style__LocationContentBlock')]//div[contains(@class, 'style__TextContainerMain')]",
                "//div[@class='style__TextContainerMain-sc-btx547-3 fObRec']",
                
                # SVG container approach (the location icon container)
                "//div[contains(@class, 'style__SvgContainer')]//parent::div//parent::div",
                
                # Generic clickable location elements
                "//div[contains(@class, 'LocationContent')]",
                "//div[contains(@class, 'location') and @role='button']",
            ]
            
            button_clicked = False
            clicked_element = None
            
            for selector in location_button_selectors:
                try:
                    # Find all matching elements
                    elements = driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        try:
                            # Check if element is visible and contains the right text
                            if element.is_displayed():
                                element_text = safe_text(element)
                                
                                # Look for "Setup your precise location" text
                                if "setup" in element_text.lower() and "location" in element_text.lower():
                                    print(f" ✓ Found button with text: '{element_text[:50]}'")
                                    
                                    # Scroll into view
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                                    time.sleep(1)
                                    
                                    # Try multiple click methods
                                    try:
                                        # Method 1: Regular click
                                        element.click()
                                        print(" ✅ Clicked using regular click")
                                        button_clicked = True
                                        clicked_element = element
                                        break
                                    except:
                                        try:
                                            # Method 2: JavaScript click
                                            driver.execute_script("arguments[0].click();", element)
                                            print(" ✅ Clicked using JavaScript click")
                                            button_clicked = True
                                            clicked_element = element
                                            break
                                        except:
                                            try:
                                                # Method 3: Action chains
                                                from selenium.webdriver.common.action_chains import ActionChains
                                                actions = ActionChains(driver)
                                                actions.move_to_element(element).click().perform()
                                                print(" ✅ Clicked using ActionChains")
                                                button_clicked = True
                                                clicked_element = element
                                                break
                                            except:
                                                continue
                        except:
                            continue
                    
                    if button_clicked:
                        break
                        
                except Exception as e:
                    continue
            
            if button_clicked:
                print(" ⏳ Waiting for input field to appear...")
                time.sleep(3)
            else:
                print(" ⚠ Could not find or click location button")
                print(" 🔍 Trying to find input field directly...")
            
            # Step 2: Find the location input field
            print(" 🔍 Looking for location input field...")
            
            location_input_selectors = [
                # Specific data-testid
                "//input[@data-testid='search_input']",
                
                # Placeholder-based
                "//input[@placeholder='Search for area, street name...']",
                "//input[contains(@placeholder, 'Search for area')]",
                "//input[contains(@placeholder, 'street name')]",
                
                # Class-based from screenshot
                "//input[contains(@class, 'style__StyledInputBox')]",
                "//div[contains(@class, 'style__Container')]//input",
                
                # Generic input fields
                "//div[contains(@class, 'LocationContainer')]//input",
                "//input[@type='text' and contains(@class, 'sc-')]",
                "//input[@type='text']",
            ]
            
            location_input = None
            
            for selector in location_input_selectors:
                try:
                    inputs = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    for inp in inputs:
                        try:
                            if inp.is_displayed() and inp.is_enabled():
                                placeholder = safe_get_attribute(inp, 'placeholder')
                                print(f" ✓ Found input field with placeholder: '{placeholder}'")
                                location_input = inp
                                break
                        except:
                            continue
                    
                    if location_input:
                        break
                        
                except:
                    continue
            
            if not location_input:
                print(f" ❌ Could not find location input field")
                if attempt < max_retries - 1:
                    print(" ↻ Retrying...")
                    # Try refreshing the page
                    driver.refresh()
                    time.sleep(3)
                    continue
                else:
                    return False
            
            # Step 3: Focus, clear and type the location
            print(f" 🎯 Interacting with input field...")
            
            # Scroll input into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", location_input)
            time.sleep(0.5)
            
            # Focus the input
            driver.execute_script("arguments[0].focus();", location_input)
            time.sleep(0.5)
            
            # Clear existing text
            try:
                location_input.clear()
            except:
                driver.execute_script("arguments[0].value = '';", location_input)
            
            time.sleep(0.5)
            
            # Type the location
            print(f" ⌨️  Typing location: {location}")
            for char in location:
                location_input.send_keys(char)
                time.sleep(0.1)
            
            print(" ⏳ Waiting for dropdown suggestions...")
            time.sleep(4)
            
            # Step 4: Select from dropdown (skip GPS option)
            print(" 🔍 Looking for location suggestions...")
            
            dropdown_selectors = [
                # Get all suggestion items (we'll filter GPS later)
                "//div[@data-testid='location_list']//div[@role='button']",
                "//div[@data-testid='location_list']//div",
                "//div[contains(@class, 'LocationListContainer')]//div[contains(@class, 'LocationItem')]",
                "//div[contains(@class, 'suggestion')]",
                "//*[@role='option']",
                "//div[contains(@class, 'location') and contains(@class, 'item')]",
            ]
            
            suggestion_clicked = False
            
            for selector in dropdown_selectors:
                try:
                    suggestions = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    print(f" ✓ Found {len(suggestions)} suggestions")
                    
                    # Filter out GPS options and find first valid suggestion
                    for idx, sugg in enumerate(suggestions):
                        try:
                            if not sugg.is_displayed():
                                continue
                                
                            text = safe_text(sugg)
                            
                            # Skip GPS/Locate me options
                            if any(keyword in text.lower() for keyword in ['gps', 'locate me', 'current location']):
                                print(f" ⏭️  Skipping: {text[:50]}")
                                continue
                            
                            # Skip empty or very short text
                            if len(text.strip()) < 3:
                                continue
                            
                            print(f" 🎯 Selecting: {text[:60]}")
                            
                            # Scroll suggestion into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sugg)
                            time.sleep(0.5)
                            
                            # Try clicking
                            try:
                                sugg.click()
                            except:
                                driver.execute_script("arguments[0].click();", sugg)
                            
                            print(f" ✅ Clicked location suggestion")
                            suggestion_clicked = True
                            time.sleep(3)
                            break
                            
                        except:
                            continue
                    
                    if suggestion_clicked:
                        break
                        
                except:
                    continue
            
            if not suggestion_clicked:
                print(" ⚠ No dropdown suggestion clicked, pressing Enter...")
                try:
                    location_input.send_keys(Keys.ENTER)
                    time.sleep(2)
                    print(" ✓ Pressed Enter")
                except:
                    print(" ⚠ Could not press Enter")
            
            # Verify location was set
            time.sleep(2)
            print(" ✅ Location setting process completed")
            return True
            
        except Exception as e:
            print(f" ❌ Error in attempt {attempt + 1}: {str(e)[:100]}")
            if attempt < max_retries - 1:
                print(" ↻ Retrying...")
                time.sleep(2)
            else:
                import traceback
                print("\n⚠️  Full error traceback:")
                traceback.print_exc()
                return False
    
    return False


def set_location_on_zomato(driver, location: str, max_retries: int = 3) -> bool:
    """Automatically set location on Zomato."""
    print(f"\n📍 Setting location on Zomato to: {location}")
    
    for attempt in range(max_retries):
        try:
            time.sleep(3)
            
            location_display_selectors = [
                "//div[contains(@class, 'sc-18n4q8v-0')]",
                "//div[contains(@class, 'gAhrnY')]",
                "//div[contains(@class, 'sc-fxmata')]",
            ]
            
            for selector in location_display_selectors:
                try:
                    location_display = driver.find_element(By.XPATH, selector)
                    driver.execute_script("arguments[0].click();", location_display)
                    print(" ✓ Clicked location display")
                    time.sleep(2)
                    break
                except:
                    continue
            
            location_selectors = [
                "//input[@placeholder='Search for restaurant, cuisine...']",
                "//input[contains(@placeholder, 'Search for restaurant')]",
                "//input[@type='text' and contains(@class, 'sc-')]",
            ]
            
            location_input = None
            for selector in location_selectors:
                try:
                    location_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if location_input and location_input.is_displayed():
                        print(f" ✓ Found Zomato search input")
                        break
                except:
                    continue
            
            if not location_input:
                if attempt < max_retries - 1:
                    print(" ↻ Retrying...")
                    time.sleep(2)
                    continue
                else:
                    return False
            
            driver.execute_script("arguments[0].focus();", location_input)
            time.sleep(0.3)
            
            try:
                location_input.clear()
            except:
                driver.execute_script("arguments[0].value = '';", location_input)
            
            time.sleep(0.5)
            
            print(f" ⌨  Typing location: {location}")
            for char in location:
                location_input.send_keys(char)
                time.sleep(0.15)
            
            time.sleep(3)
            
            dropdown_selectors = [
                "//div[contains(@class, 'sc-') and @role='button' and contains(., ',')]",
                "//div[@class and contains(@class, 'sc-') and contains(text(), ',')]",
            ]
            
            dropdown_clicked = False
            for selector in dropdown_selectors:
                try:
                    suggestions = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    if suggestions:
                        valid_suggestions = []
                        for sugg in suggestions:
                            text = sugg.text.strip()
                            if text and "current location" not in text.lower() and "," in text:
                                valid_suggestions.append(sugg)
                        
                        if valid_suggestions:
                            first_suggestion = valid_suggestions[0]
                            suggestion_text = first_suggestion.text.strip()
                            driver.execute_script("arguments[0].click();", first_suggestion)
                            print(f" ✅ Clicked location: {suggestion_text[:60]}")
                            dropdown_clicked = True
                            time.sleep(3)
                            break
                except:
                    continue
            
            if not dropdown_clicked:
                location_input.send_keys(Keys.ENTER)
                time.sleep(2)
            
            print(" ✅ Location setting completed on Zomato")
            return True
            
        except Exception as e:
            print(f" ⚠ Attempt {attempt + 1}/{max_retries} failed")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False
    
    return False


def extract_zomato_card_data(card) -> Dict:
    """Extract data from Zomato restaurant cards."""
    data = {
        "name": "",
        "cuisine": "",
        "price_for_two": "",
        "rating": ""
    }
    
    card_text = safe_text(card)
    
    if len(card_text) < 20:
        return data
    
    # Extract name
    name_selectors = [
        ".//h4[contains(@class, 'sc-')]",
        ".//a//h4",
        ".//div[contains(@class, 'sc-')]//h4",
        ".//h3",
        ".//h2",
    ]
    
    for selector in name_selectors:
        name_el = safe_find(card, By.XPATH, selector)
        if name_el:
            text = safe_text(name_el)
            if (text and len(text) > 2 and len(text) < 100 and
                not text.replace(".", "").isdigit() and
                "₹" not in text and "km" not in text.lower()):
                data["name"] = text
                break
    
    if not data["name"]:
        lines = [l.strip() for l in card_text.split('\n') if l.strip() and len(l.strip()) > 3]
        for line in lines[:5]:
            if (len(line) < 100 and "₹" not in line and 
                "km" not in line.lower() and not line.replace(".", "").isdigit()):
                data["name"] = line
                break
    
    # Extract rating - Enhanced extraction
    rating_selectors = [
        ".//div[contains(@class, 'rating')]",
        ".//span[contains(@class, 'rating')]",
        ".//div[contains(@aria-label, 'rating')]",
        ".//span[contains(@aria-label, 'rating')]",
    ]
    
    for selector in rating_selectors:
        rating_el = safe_find(card, By.XPATH, selector)
        if rating_el:
            rating_text = safe_text(rating_el)
            rating_match = re.search(r'\b([0-5]\.\d)\b', rating_text)
            if rating_match:
                rating_val = rating_match.group(1)
                try:
                    if 0 <= float(rating_val) <= 5:
                        data["rating"] = rating_val
                        break
                except:
                    pass
    
    # Fallback: search all divs for rating-like numbers
    if not data["rating"]:
        all_divs = card.find_elements(By.XPATH, ".//div | .//span")
        for div in all_divs:
            text = safe_text(div)
            if re.fullmatch(r'[0-5]\.\d', text):
                try:
                    if 0 <= float(text) <= 5:
                        data["rating"] = text
                        break
                except:
                    pass
    
    # Final fallback: regex on card text
    if not data["rating"]:
        rating_matches = re.findall(r'\b([0-5]\.\d)\b', card_text)
        if rating_matches:
            data["rating"] = rating_matches[0]
    
    # Extract cuisine
    cuisine_patterns = [
        r'([A-Za-z\s]+,\s*[A-Za-z\s,]+)(?=\s*₹|\s*\d+\s*km|\s*\d+\s*min|$)',
        r'([A-Za-z\s]+•[A-Za-z\s•]+)',
    ]
    
    for pattern in cuisine_patterns:
        cuisine_match = re.search(pattern, card_text)
        if cuisine_match:
            cuisine_text = cuisine_match.group(1).strip()
            if (cuisine_text != data["name"] and len(cuisine_text) < 100 and len(cuisine_text) > 3):
                cuisines = [c.strip() for c in re.split(r'[,•]', cuisine_text)]
                cuisines = [c for c in cuisines if c and len(c) > 1]
                if cuisines:
                    data["cuisine"] = ", ".join(cuisines[:5])
                    break
    
    # Extract price
    price_patterns = [
        r'₹\s*([\d,]+)\s*for\s*(?:two|2)',
        r'for\s*(?:two|2)\s*₹\s*([\d,]+)',
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, card_text, re.IGNORECASE)
        if price_match:
            data["price_for_two"] = f"₹{price_match.group(1)} for two"
            break
    
    # Clean up
    for k, v in list(data.items()):
        if isinstance(v, str):
            data[k] = v.replace("\n", " ").replace("  ", " ").strip()
    
    return data


def extract_swiggy_card_data(card) -> Dict:
    """Extract data from Swiggy Dineout restaurant cards."""
    data = {
        "name": "",
        "cuisines": "",
        "price_for_two": "",
        "rating": ""
    }
    
    card_text = safe_text(card)
    
    if len(card_text) < 20:
        return data
    
    # Extract name using multiple strategies
    name_selectors = [
        # Based on screenshot - restaurant name classes
        ".//div[contains(@class, 'sc-khjjjR')]",
        ".//div[contains(@class, 'sc-') and contains(@class, 'ebUBjR')]",
        
        # Standard heading tags
        ".//h3", ".//h2", ".//h4",
        
        # Common Swiggy restaurant name patterns
        ".//div[contains(@class, 'RestaurantName')]",
        ".//div[contains(@class, 'restaurant-name')]",
        ".//a[contains(@href, '/restaurants/')]//div",
    ]
    
    for selector in name_selectors:
        try:
            name_elements = card.find_elements(By.XPATH, selector)
            for elem in name_elements:
                text = safe_text(elem)
                # Valid name criteria
                if (text and 
                    len(text) > 2 and 
                    len(text) < 100 and 
                    "for two" not in text.lower() and
                    "₹" not in text and 
                    "km" not in text.lower() and
                    not text.replace(".", "").replace(",", "").isdigit() and
                    "flex" not in text.lower()):
                    data["name"] = text
                    break
            
            if data["name"]:
                break
        except:
            continue
    
    # Fallback: parse from card text
    if not data["name"]:
        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
        for line in lines[:5]:  # Check first 5 lines
            if (len(line) > 2 and 
                len(line) < 100 and 
                "for two" not in line.lower() and 
                "₹" not in line and 
                "km" not in line.lower() and
                "flex" not in line.lower() and
                not line.replace(".", "").isdigit()):
                data["name"] = line
                break
    
    # Extract rating - Enhanced extraction based on screenshot
    rating_selectors = [
        # Based on screenshot - rating classes
        ".//div[contains(@class, 'sc-khjjjR') and contains(@class, 'fUBKND')]",
        ".//div[contains(@class, 'fUBKND')]",
        
        # Generic rating patterns
        ".//div[contains(@class, 'rating')]",
        ".//span[contains(@class, 'rating')]",
        ".//div[contains(@class, 'sc-') and contains(@class, 'rating')]",
        
        # Star icon nearby
        ".//svg[@width='16' and @height='16']//parent::div//following-sibling::div",
    ]
    
    for selector in rating_selectors:
        try:
            rating_elements = card.find_elements(By.XPATH, selector)
            for elem in rating_elements:
                text = safe_text(elem)
                # Match rating pattern: single digit.decimal (e.g., 4.2, 3.8)
                rating_match = re.search(r'\b([0-5]\.\d)\b', text)
                if rating_match:
                    rating_val = rating_match.group(1)
                    try:
                        if 0 <= float(rating_val) <= 5:
                            data["rating"] = rating_val
                            break
                    except:
                        pass
            
            if data["rating"]:
                break
        except:
            continue
    
    # Fallback: search in card text for rating pattern
    if not data["rating"]:
        rating_matches = re.findall(r'\b([0-5]\.\d)\b', card_text)
        for rating_val in rating_matches:
            try:
                if 0 <= float(rating_val) <= 5:
                    data["rating"] = rating_val
                    break
            except:
                pass
    
    # Extract price
    price_match = re.search(r'₹\s*[\d,]+\s*for\s*two', card_text, re.IGNORECASE)
    if price_match:
        data["price_for_two"] = price_match.group(0)
    
    # Extract cuisines
    cuisines_patterns = [
        r'([A-Za-z\s]+•[A-Za-z\s•]+)',  # Bullet separated
        r'([A-Za-z\s]+,\s*[A-Za-z\s,]+)(?=\s*₹|\s*\d+\s*km)',  # Comma separated before price/distance
    ]
    
    for pattern in cuisines_patterns:
        cuisines_match = re.search(pattern, card_text)
        if cuisines_match:
            cuisine_text = cuisines_match.group(1).strip()
            # Filter out if it's the restaurant name
            if cuisine_text != data["name"] and len(cuisine_text) > 3:
                data["cuisines"] = cuisine_text
                break
    
    # Clean up
    for k, v in list(data.items()):
        if isinstance(v, str):
            data[k] = v.replace("\n", " ").strip()
    
    return data


def scrape_zomato_restaurants(driver, max_cards: int = 100) -> List[Dict]:
    """Scrape Zomato restaurant cards."""
    print("\n🍽 Starting Zomato restaurant scraping...")
    
    scroll_and_load_content(driver, max_scrolls=5)
    
    card_selectors = [
        "//div[contains(@class, 'jumbo-tracker') and .//a[contains(@href, '/restaurant')]]",
        "//div[contains(@class, 'sc-') and .//h4 and .//img]",
        "//article[contains(@class, 'sc-')]",
    ]
    
    cards = []
    for selector in card_selectors:
        try:
            cards = driver.find_elements(By.XPATH, selector)
            if cards and len(cards) > 3:
                print(f" ✓ Found {len(cards)} restaurant cards")
                break
        except:
            continue
    
    if not cards:
        cards = detect_card_elements(driver)
    
    print(f"📦 Processing {min(len(cards), max_cards)} cards...\n")
    
    seen = set()
    rows = []
    
    for card in cards[:max_cards]:
        try:
            row = extract_zomato_card_data(card)
            
            if not row.get("name") or len(row.get("name", "")) < 2:
                continue
            
            key = (row.get("name"), row.get("price_for_two"), row.get("cuisine"))
            if key in seen:
                continue
            seen.add(key)
            
            rows.append(row)
            
            name = row.get('name', 'N/A')[:50]
            cuisine = row.get('cuisine', 'N/A')[:40]
            price = row.get('price_for_two', 'N/A')[:20]
            rating = row.get('rating', 'N/A')
            
            # Add star emoji for rating display
            rating_display = f"⭐ {rating}" if rating != 'N/A' else "⭐ --"
            
            print(f"✅ [{len(rows):3d}] 🏨 {name:<50} | {cuisine:<40} | {price:<20} | {rating_display}")
            
        except:
            continue
    
    print(f"\n📊 Total restaurants scraped: {len(rows)}")
    print(f"🏨 Unique restaurant names extracted")
    
    # Show rating statistics
    ratings = [float(r.get('rating', 0)) for r in rows if r.get('rating') and r.get('rating') != 'N/A']
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        print(f"⭐ Average rating: {avg_rating:.2f}")
        print(f"⭐ Highest rating: {max(ratings):.1f}")
        print(f"⭐ Lowest rating: {min(ratings):.1f}")
        print(f"⭐ Restaurants with ratings: {len(ratings)}/{len(rows)}")
    print()
    
    return rows


def scrape_swiggy_restaurants(driver, max_cards: int = 100) -> List[Dict]:
    """Scrape Swiggy Dineout restaurant cards."""
    print("\n🍽 Starting Swiggy restaurant scraping...")
    
    scroll_and_load_content(driver, max_scrolls=5)
    
    # Updated card selectors based on screenshot structure
    card_selectors = [
        # From screenshot: Links to restaurants
        "//a[contains(@href, '/restaurants/') and contains(@href, '/dineout')]",
        
        # Generic restaurant card containers
        "//div[contains(@class, 'RestaurantCard')]",
        "//div[contains(@class, 'restaurant-card')]",
        
        # Cards containing "for two" text
        "//div[contains(@class, 'sc-') and .//div[contains(text(),'for two')]]",
        
        # Links with restaurant class
        "//a[contains(@class, 'sc-') and contains(@href, '/restaurants/')]",
    ]
    
    cards = []
    for selector in card_selectors:
        try:
            cards = driver.find_elements(By.XPATH, selector)
            if cards and len(cards) > 3:
                print(f" ✓ Found {len(cards)} restaurant cards using selector: {selector[:50]}")
                break
        except:
            continue
    
    if not cards:
        print(" ⚠ Using fallback card detection...")
        cards = detect_card_elements(driver)
    
    print(f"📦 Processing {min(len(cards), max_cards)} cards...\n")
    
    seen = set()
    rows = []
    
    for idx, card in enumerate(cards[:max_cards], 1):
        try:
            row = extract_swiggy_card_data(card)
            
            # Skip if no name found
            if not row.get("name") or len(row.get("name", "")) < 2:
                continue
            
            # Skip duplicates
            key = (row.get("name"), row.get("price_for_two"))
            if key in seen:
                continue
            seen.add(key)
            
            rows.append(row)
            
            # Display extracted data
            name = row.get('name', 'N/A')[:50]
            cuisines = row.get('cuisines', 'N/A')[:35]
            price = row.get('price_for_two', 'N/A')[:20]
            rating = row.get('rating', 'N/A')
            
            # Add star emoji for rating display
            rating_display = f"⭐ {rating}" if rating != 'N/A' else "⭐ --"
            
            print(f"✅ [{len(rows):3d}] 🏨 {name:<50} | {cuisines:<35} | {price:<20} | {rating_display}")
            
        except Exception as e:
            continue
    
    print(f"\n📊 Total restaurants scraped: {len(rows)}")
    print(f"🏨 Unique restaurant names extracted")
    
    # Show rating statistics
    ratings = [float(r.get('rating', 0)) for r in rows if r.get('rating') and r.get('rating') != 'N/A']
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        print(f"⭐ Average rating: {avg_rating:.2f}")
        print(f"⭐ Highest rating: {max(ratings):.1f}")
        print(f"⭐ Lowest rating: {min(ratings):.1f}")
        print(f"⭐ Restaurants with ratings: {len(ratings)}/{len(rows)}")
    print()
    
    return rows


def save_to_csv(rows: List[Dict], business_name: str = "scraped_data"):
    """Save scraped data to CSV file."""
    if not rows:
        print("❌ No results to save.")
        return
    
    df = pd.DataFrame(rows)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_')
    filename = f"scraped_{safe_name}_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"💾 Saved {len(df)} rows to {filename}")


def scrape_swiggy(business_name: str, location: str, max_results: int = 50) -> List[Dict]:
    """
    Main scraping function to be called from scraper_node.py.
    
    Args:
        business_name: Type of business (cafe, restaurant)
        location: Location to search
        max_results: Maximum number of results to return
        
    Returns:
        List of scraped restaurant data dictionaries
    """
    print(f"\n🍽️ Starting Swiggy scraper for: {business_name} in {location}")
    
    # Build query
    query = f"{business_name} near {location}"
    
    # Extract location info
    location_info = extract_location_from_query(query)
    
    # Search for URL using Serper API
    url = search_business_with_serper(query)
    
    # If no URL found, use default Swiggy Dineout
    if not url:
        print("⚠️ No specific URL found, using default Swiggy Dineout")
        url = "https://www.swiggy.com/dineout/restaurants"
    
    # Detect platform
    if "swiggy" in url.lower():
        platform = "swiggy"
    elif "zomato" in url.lower():
        platform = "zomato"
    else:
        platform = "swiggy"
    
    print(f"🌐 Platform: {platform}")
    print(f"🔗 URL: {url}")
    
    # Initialize browser
    driver = make_driver(headless=True)
    
    try:
        # Navigate to URL
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Set location if available
        if location_info.get("location"):
            print(f"📍 Setting location: {location_info['location']}")
            if platform == "swiggy":
                success = set_location_on_swiggy(driver, location_info['location'])
                if not success:
                    print("⚠️ Location setting failed, continuing with default location")
            elif platform == "zomato":
                success = set_location_on_zomato(driver, location_info['location'])
                if not success:
                    print("⚠️ Location setting failed, continuing with default location")
        
        # Scrape based on platform
        if platform == "zomato":
            rows = scrape_zomato_restaurants(driver, max_cards=max_results)
        else:
            rows = scrape_swiggy_restaurants(driver, max_cards=max_results)
        
        print(f"✅ Scraped {len(rows)} restaurants")
        return rows
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        try:
            driver.quit()
            print("🔒 Browser closed")
        except:
            pass


def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("🌐 RESTAURANT SCRAPER WITH AUTO-LOCATION")
    print("="*80 + "\n")
    
    # Get query from command line or user input
    business_name = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    
    if not business_name:
        business_name = input("Enter query (e.g., 'Restaurants near homeland regalia'): ").strip()
    
    if not business_name:
        print("❌ No query provided. Exiting.")
        return
    
    print(f"\n🔍 Processing: {business_name}")
    
    # Extract location
    location_info = extract_location_from_query(business_name)
    
    print(f"\n🎯 Query Analysis:")
    print(f"   Search Term: {location_info['search_term']}")
    print(f"   Location: {location_info['location'] if location_info['location'] else 'Not specified'}")
    
    # Try Serper API first
    url = search_business_with_serper(business_name)
    
    # If Serper fails, manual selection
    if not url:
        print("\n📋 Select platform:")
        print("   1. Swiggy Dineout")
        print("   2. Zomato")
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            url = "https://www.swiggy.com/dineout/restaurants"
            platform = "swiggy"
        elif choice == '2':
            url = "https://www.zomato.com/indore/restaurants"
            platform = "zomato"
        else:
            print("❌ Invalid choice. Exiting.")
            return
    else:
        # Detect platform from URL
        if "swiggy" in url.lower():
            platform = "swiggy"
        elif "zomato" in url.lower():
            platform = "zomato"
        else:
            print("⚠ Unknown platform. Defaulting to Swiggy.")
            platform = "swiggy"
    
    # Initialize browser
    print("\n🚀 Launching browser...")
    driver = make_driver(headless=False)
    
    try:
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Handle location setting
        if location_info.get("location"):
            print(f"\n🎯 Location detected: {location_info['location']}")
            if platform == "swiggy":
                success = set_location_on_swiggy(driver, location_info['location'])
                if not success:
                    print("⚠ Location setting failed, continuing with current location...")
            elif platform == "zomato":
                success = set_location_on_zomato(driver, location_info['location'])
                if not success:
                    print("⚠ Location setting failed, continuing with current location...")
        else:
            print("\n⚠ No location specified in query, using default location")
        
        # Scrape based on platform
        if platform == "zomato":
            rows = scrape_zomato_restaurants(driver, max_cards=100)
        else:
            rows = scrape_swiggy_restaurants(driver, max_cards=100)
        
        # Save results
        if rows:
            save_to_csv(rows, business_name)
            print("\n✅ Scraping completed successfully!")
        else:
            print("\n⚠ No data scraped.")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
            print("🔒 Browser closed.")
        except:
            pass


if __name__ == "__main__":
    main()