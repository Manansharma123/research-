"""
Universal Scraper for Booking.com - Integrated with Business Advisor Project
This scraper handles hotel/accommodation searches on Booking.com with automated search functionality.
"""

import time
import sys
import re
import os
import json
import random
import requests
from typing import List, Dict, Optional, Any
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Serper API Configuration
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
SERPER_API_URL = "https://google.serper.dev/search"

def make_driver(headless: bool = True) -> webdriver.Chrome:
    """Initialize Chrome WebDriver with optimal settings. Runs in headless mode by default (no browser window visible)."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")  # Set window size for headless
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
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

def click_element_safely(driver, element, method="javascript"):
    """Try multiple methods to click an element."""
    methods = ["javascript", "action_chains", "direct"]
    if method in methods:
        methods = [method] + [m for m in methods if m != method]
    
    for m in methods:
        try:
            if m == "javascript":
                driver.execute_script("arguments[0].click();", element)
                return True
            elif m == "action_chains":
                ActionChains(driver).move_to_element(element).click().perform()
                return True
            elif m == "direct":
                element.click()
                return True
        except Exception as e:
            continue
    return False

def search_business_with_serper(business_name: str) -> Optional[str]:
    """
    OPTIONAL: Use Serper API to search for a business and return its URL.
    Only used for non-hotel businesses if you want automated URL discovery.
    For hotels, we go directly to Booking.com, so this is NOT needed.
    
    Note: This function is kept for backward compatibility but is optional.
    """
    if not SERPER_API_KEY:
        logger.info("ℹ️  Serper API not configured (optional - not needed for hotels)")
        return None
    
    search_query = f"{business_name} (in India)"
    
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
        logger.info(f"🌐 Searching via Serper API: {search_query}")
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        organic_results = data.get('organic', [])
        
        if not organic_results:
            logger.warning("❌ No results found.")
            return None
        
        selected_url = organic_results[0].get('link')
        selected_title = organic_results[0].get('title', 'N/A')
        
        logger.info(f"✅ Found: {selected_title}")
        logger.info(f"🔗 URL: {selected_url}")
        
        return selected_url
    
    except Exception as e:
        logger.error(f"❌ Error calling Serper API: {e}")
        return None

def scrape_universal_cards(driver, url: str = "") -> List[Dict]:
    """
    Universal card scraping for non-hotel businesses.
    Required for general business scraping.
    """
    logger.info("\n🔍 Detecting card elements on the page...")
    
    # Simple card detection
    cards = []
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='card'], div[class*='item'], article")
        cards = [c for c in cards if len(safe_text(c)) > 50][:50]
    except:
        pass
    
    logger.info(f"📦 Found {len(cards)} potential card elements\n")
    
    results = []
    seen = set()
    
    for card in cards:
        try:
            card_text = safe_text(card)
            if len(card_text) < 30:
                continue
            
            # Extract basic data
            data = {
                "name": "",
                "price": "",
                "rating": "",
                "description": card_text[:200]
            }
            
            # Extract name from heading
            for tag in ['h1', 'h2', 'h3', 'h4']:
                heading = safe_find(card, By.TAG_NAME, tag)
                if heading:
                    data["name"] = safe_text(heading)
                    break
            
            if not data["name"]:
                lines = card_text.split('\n')
                data["name"] = lines[0][:100] if lines else ""
            
            # Extract price
            price_match = re.search(r'[$₹€£¥]\s*[\d,]+', card_text)
            if price_match:
                data["price"] = price_match.group(0)
            
            # Extract rating
            rating_match = re.search(r'(\d+\.\d+)\s*(?:stars?|★|⭐|/5)', card_text, re.IGNORECASE)
            if rating_match:
                data["rating"] = rating_match.group(1)
            
            if data["name"] and data["name"] not in seen:
                seen.add(data["name"])
                results.append(data)
                logger.info(f"✅ [{len(results)}] {data['name'][:50]}")
        
        except Exception:
            continue
    
    logger.info(f"\n📊 Total items scraped: {len(results)}\n")
    return results

def wait_for_calendar_to_open(driver, timeout=5):
    """Wait and verify that the calendar actually opened."""
    logger.info("⏳ Waiting for calendar to appear...")
    time.sleep(1)
    
    calendar_selectors = [
        "//div[@data-testid='searchbox-datepicker-calendar']",
        "//div[@role='dialog' and contains(@class, 'calendar')]",
        "//div[contains(@class, 'calendar-wrapper')]",
        "//div[@class='calendar']"
    ]
    
    end_time = time.time() + timeout
    while time.time() < end_time:
        for selector in calendar_selectors:
            try:
                calendar = driver.find_element(By.XPATH, selector)
                if calendar and calendar.is_displayed():
                    logger.info("✅ Calendar is now visible!")
                    return True
            except:
                pass
        time.sleep(0.5)
    
    return False

def search_on_booking(driver, location: str) -> bool:
    """
    Navigate to Booking.com, enter location, select dates, and search.
    Returns True if search was successful, False otherwise.
    """
    try:
        logger.info("\n🌐 Opening Booking.com...")
        driver.get("https://www.booking.com/index.en-gb.html")
        time.sleep(4)
        
        # Close any popups/cookie banners
        try:
            close_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'Close') or contains(@aria-label, 'Dismiss')]")
            for btn in close_buttons[:3]:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        
        logger.info(f"🔍 Searching for: {location}")
        
        wait = WebDriverWait(driver, 15)
        
        # Find and fill the location search input
        search_input = None
        selectors = [
            "//input[@placeholder='Where are you going?']",
            "//input[@name='ss']",
            "//input[@id='ss']",
            "//input[contains(@placeholder, 'going')]"
        ]
        
        for selector in selectors:
            try:
                search_input = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if search_input:
                    break
            except:
                continue
        
        if not search_input:
            logger.error("❌ Could not find search input field")
            return False
        
        logger.info("📝 Entering location...")
        search_input.click()
        time.sleep(1)
        search_input.clear()
        time.sleep(0.5)
        
        for char in location:
            search_input.send_keys(char)
            time.sleep(0.08)
        
        time.sleep(2.5)
        
        # Select first autocomplete option
        logger.info("🎯 Selecting from dropdown...")
        autocomplete_selectors = [
            "//li[@data-i='0']",
            "//ul[@role='listbox']//li[1]",
            "(//li[contains(@id, 'autocomplete-result')])[1]",
            "//div[@role='option'][1]"
        ]
        
        location_selected = False
        for selector in autocomplete_selectors:
            try:
                first_option = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].click();", first_option)
                logger.info("✅ Location selected from dropdown")
                location_selected = True
                time.sleep(1.5)
                break
            except:
                continue
        
        if not location_selected:
            logger.warning("⚠️  Could not select from dropdown, trying keyboard navigation")
            try:
                search_input.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                search_input.send_keys(Keys.ENTER)
                logger.info("✅ Location entered via keyboard")
                time.sleep(1.5)
            except:
                pass
        
        # Now handle the date picker - CRITICAL FIX
        logger.info("\n📅 Opening date calendar...")
        
        date_button_selectors = [
            "//button[@data-testid='searchbox-dates-container']",
            "//div[@data-testid='searchbox-dates-container']",
            "//button[contains(@id, 'calendar-searchboxdatepicker')]",
            "//div[@class='ed9f289288']",
            "//button[contains(@class, 'de576f5064')]"
        ]
        
        calendar_opened = False
        date_button = None
        
        for selector in date_button_selectors:
            try:
                logger.info(f"   Trying selector: {selector}")
                date_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                
                if date_button:
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_button)
                    time.sleep(0.5)
                    
                    # Try to click
                    logger.info("   Attempting to click date picker...")
                    if click_element_safely(driver, date_button):
                        time.sleep(1.5)
                        
                        # VERIFY the calendar opened
                        if wait_for_calendar_to_open(driver, timeout=5):
                            calendar_opened = True
                            break
                        else:
                            logger.warning("   ⚠️  Calendar didn't open, trying next method...")
            except Exception as e:
                logger.warning(f"   ⚠️  Failed with selector: {e}")
                continue
        
        # Alternative method: Use keyboard navigation
        if not calendar_opened:
            logger.warning("⚠️  Trying keyboard method to open calendar...")
            try:
                # Tab from search input to date field
                search_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                
                # Press Enter or Space to activate date picker
                actions = ActionChains(driver)
                actions.send_keys(Keys.SPACE).perform()
                time.sleep(1.5)
                
                if wait_for_calendar_to_open(driver):
                    calendar_opened = True
                    logger.info("✅ Calendar opened via keyboard!")
            except Exception as e:
                logger.warning(f"   Keyboard method failed: {e}")
        
        if not calendar_opened:
            logger.error("❌ CRITICAL: Could not open calendar after all attempts")
            logger.info("🔍 Taking screenshot for debugging...")
            driver.save_screenshot("debug_no_calendar.png")
            return False
        
        # NOW select dates - calendar is confirmed open
        logger.info("\n🗓️  Selecting check-in and check-out dates...")
        time.sleep(1)
        
        # Find available dates (not disabled or in the past)
        available_dates = driver.find_elements(By.XPATH, 
            "//span[@data-date and not(contains(@aria-disabled, 'true')) and not(ancestor::td[contains(@class, 'disabled')])]"
        )
        
        if len(available_dates) < 2:
            # Try alternative selector
            available_dates = driver.find_elements(By.XPATH,
                "//td[not(contains(@class, 'disabled'))]//span[@data-date]"
            )
        
        logger.info(f"   Found {len(available_dates)} available dates")
        
        if len(available_dates) >= 5:
            try:
                # Select check-in (3rd available date - few days from now)
                checkin = available_dates[2]
                checkin_date = checkin.get_attribute('data-date')
                
                driver.execute_script("arguments[0].scrollIntoView(true);", checkin)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", checkin)
                logger.info(f"✅ Check-in: {checkin_date}")
                time.sleep(1)
                
                # Refresh available dates after first click
                available_dates = driver.find_elements(By.XPATH, 
                    "//span[@data-date and not(contains(@aria-disabled, 'true'))]"
                )
                
                # Select check-out (few days after check-in)
                if len(available_dates) >= 6:
                    checkout = available_dates[5]
                    checkout_date = checkout.get_attribute('data-date')
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkout)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", checkout)
                    logger.info(f"✅ Check-out: {checkout_date}")
                    time.sleep(1.5)
                else:
                    logger.warning("⚠️  Not enough dates for check-out")
                    
            except Exception as e:
                logger.error(f"❌ Error selecting dates: {e}")
                driver.save_screenshot("debug_date_selection.png")
                return False
        else:
            logger.error("❌ Not enough available dates found")
            return False
        
        # Click Search button
        logger.info("\n🔍 Clicking search button...")
        time.sleep(1)
        
        search_buttons = [
            "//button[@type='submit']//span[contains(text(), 'Search')]",
            "//button[@type='submit' and contains(., 'Search')]",
            "//button[@type='submit']",
            "//span[text()='Search']/parent::button"
        ]
        
        for btn_selector in search_buttons:
            try:
                search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, btn_selector)))
                driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", search_btn)
                logger.info("✅ Search button clicked!")
                time.sleep(6)
                return True
            except:
                continue
        
        logger.error("❌ Could not click search button")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("debug_error.png")
        return False

def _get_scroll_height(driver) -> int:
    """Get current scroll height of the page."""
    try:
        return int(driver.execute_script("return document.body.scrollHeight || document.documentElement.scrollHeight || 0;"))
    except Exception:
        return 0

def scroll_and_load_content(driver, max_scrolls: int = 8):
    """Scroll the page to load dynamic content."""
    logger.info("\n📜 Scrolling to load all results...")
    
    last_height = _get_scroll_height(driver)
    scrolls = 0
    
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = _get_scroll_height(driver)
        if new_height == last_height:
            scrolls += 1
        else:
            scrolls = 0
            last_height = new_height
    
    logger.info("✅ Finished loading content\n")

def extract_hotel_data(card) -> Dict:
    """Extract hotel data from card element."""
    data = {
        "name": "",
        "price": "",
        "rating": "",
        "amenities": "",
        "location": ""
    }
    
    try:
        card_text = safe_text(card)
        
        if len(card_text) < 30 or "Filter" in card_text:
            return data
        
        # Extract hotel name
        name_selectors = [
            ".//div[@data-testid='title']",
            ".//h3",
            ".//h2",
            ".//div[contains(@class, 'title')]//div",
            ".//a[contains(@data-testid, 'title')]"
        ]
        
        for selector in name_selectors:
            name_elem = safe_find(card, By.XPATH, selector)
            if name_elem:
                name = safe_text(name_elem)
                if name and len(name) > 3:
                    data["name"] = name.strip()
                    break
        
        # Extract price
        price_selectors = [
            ".//span[@data-testid='price-and-discounted-price']",
            ".//div[@data-testid='price-and-discounted-price']",
            ".//span[contains(@class, 'price')]",
            ".//*[contains(text(), '₹')]"
        ]
        
        for selector in price_selectors:
            price_elem = safe_find(card, By.XPATH, selector)
            if price_elem:
                price_text = safe_text(price_elem)
                price_match = re.search(r'₹\s*[\d,]+', price_text)
                if price_match:
                    data["price"] = price_match.group(0)
                    break
        
        if not data["price"]:
            price_match = re.search(r'₹\s*[\d,]+', card_text)
            if price_match:
                data["price"] = price_match.group(0)
        
        # Extract rating
        rating_selectors = [
            ".//div[@data-testid='review-score']//div[contains(@class, 'review-score')]",
            ".//div[contains(@aria-label, 'Scored')]",
            ".//*[contains(text(), 'Scored')]",
            ".//div[contains(@class, 'rating')]"
        ]
        
        for selector in rating_selectors:
            rating_elem = safe_find(card, By.XPATH, selector)
            if rating_elem:
                rating_text = safe_text(rating_elem)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    data["rating"] = rating_match.group(1)
                    break
        
        if not data["rating"]:
            rating_patterns = [
                r'Scored\s+(\d+\.?\d*)',
                r'(\d+\.\d+)\s+(?:out of|/)',
                r'Rating\s+(\d+\.?\d*)'
            ]
            for pattern in rating_patterns:
                match = re.search(pattern, card_text, re.IGNORECASE)
                if match:
                    data["rating"] = match.group(1)
                    break
        
        # Extract amenities
        amenities_list = []
        amenity_keywords = ['WiFi', 'Parking', 'Pool', 'Spa', 'Gym', 'Restaurant', 'Breakfast', 
                           'Air conditioning', 'Room service', 'Bar', 'Fitness']
        
        for keyword in amenity_keywords:
            if keyword.lower() in card_text.lower():
                amenities_list.append(keyword)
        
        if amenities_list:
            data["amenities"] = ", ".join(amenities_list[:6])
        
        # Extract location
        location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:Mumbai|Delhi|Bangalore|India)', card_text)
        if location_match:
            data["location"] = location_match.group(1)
        
    except Exception:
        pass
    
    return data

def scrape_results(driver) -> List[Dict]:
    """Scrape hotel results from search results page."""
    logger.info("\n🔍 Detecting hotel cards...")
    
    time.sleep(3)
    
    card_selectors = [
        "//div[@data-testid='property-card']",
        "//div[contains(@data-testid, 'property')]",
        "//div[contains(@class, 'property-card')]",
        "//div[@data-testid='property-card-container']"
    ]
    
    cards = []
    for selector in card_selectors:
        try:
            cards = driver.find_elements(By.XPATH, selector)
            if cards and len(cards) > 0:
                logger.info(f"✅ Found cards using selector: {selector}")
                break
        except:
            continue
    
    if not cards:
        logger.warning("⚠️  No property cards found, trying alternative method...")
        cards = driver.find_elements(By.XPATH, "//div[contains(., '₹') and .//h3]")
    
    valid_cards = []
    for card in cards:
        text = safe_text(card)
        if text and len(text) > 50 and "Filter" not in text:
            valid_cards.append(card)
    
    cards = valid_cards[:50]
    
    logger.info(f"📦 Found {len(cards)} hotel cards\n")
    
    if len(cards) == 0:
        logger.warning("⚠️  No valid cards found. The page might not have loaded properly.")
        return []
    
    seen = set()
    results = []
    
    logger.info("🔄 Extracting data from cards...\n")
    
    for idx, card in enumerate(cards, 1):
        try:
            hotel_data = extract_hotel_data(card)
            
            if not hotel_data["name"] or len(hotel_data["name"]) < 3:
                continue
            
            key = hotel_data["name"]
            if key in seen:
                continue
            seen.add(key)
            
            results.append(hotel_data)
            
            name = hotel_data.get('name', 'N/A')[:50]
            price = hotel_data.get('price', 'N/A')
            rating = hotel_data.get('rating', 'N/A')
            amenities = hotel_data.get('amenities', 'N/A')[:40]
            
            logger.info(f"✅ [{len(results)}] {name}")
            logger.info(f"    💰 {price}  |  ⭐ {rating}  |  🏨 {amenities}\n")
            
        except Exception:
            continue
    
    logger.info(f"📊 Total hotels scraped: {len(results)}\n")
    return results

def save_to_csv(rows: List[Dict], location: str):
    """
    Optional: Save scraped data to CSV file for debugging/backup purposes.
    Note: In production, data is passed directly to LLM for analysis.
    """
    if not rows:
        logger.warning("❌ No results found to save.")
        return
    
    df = pd.DataFrame(rows)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_location = re.sub(r'[^\w\s-]', '', location).strip().replace(' ', '_')
    filename = f"booking_{safe_location}_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    logger.info(f"💾 Saved {len(df)} hotels to: {filename}")
    return filename

def scrape_booking_hotels(location: str, headless: bool = True) -> List[Dict]:
    """
    Main function to scrape Booking.com hotels for a given location.
    This is the entry point for integration with the Business Advisor project.
    
    Args:
        location: Location to search for hotels (e.g., "Mumbai", "Delhi hotels")
        headless: Whether to run browser in headless mode (default: True)
    
    Returns:
        List of dictionaries containing hotel data
    """
    logger.info("\n" + "="*80)
    logger.info("🏨 BOOKING.COM HOTEL SCRAPER")
    logger.info("="*80 + "\n")
    
    logger.info(f"🚀 Starting search for: {location}")
    driver = make_driver(headless=headless)
    
    try:
        success = search_on_booking(driver, location)
        
        if not success:
            logger.error("❌ Search failed. Exiting.")
            return []
        
        logger.info("\n⏳ Waiting for results to load...")
        time.sleep(5)
        
        scroll_and_load_content(driver, max_scrolls=6)
        
        results = scrape_results(driver)
        
        if results:
            logger.info("\n✅ Scraping completed successfully!")
        else:
            logger.warning("\n⚠️  No results found. Check if the search page loaded correctly.")
        
        return results
        
    except Exception as e:
        logger.error(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            driver.quit()
            logger.info("🔒 Browser closed.")
        except Exception:
            pass

def main():
    """Main execution function for standalone usage (testing/debugging only)."""
    print("\n" + "="*80)
    print("🏨 BOOKING.COM AUTOMATED SEARCH & SCRAPER")
    print("="*80 + "\n")
    
    location = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not location:
        location = input("Enter location to search (e.g., 'Mumbai hotels', 'Paris'): ").strip()
    
    if not location:
        print("❌ No location provided. Exiting.")
        return
    
    results = scrape_booking_hotels(location, headless=True)
    
    if results:
        # Optional: Save to CSV for debugging purposes
        save_to_csv(results, location)
        print("\n✅ Scraping completed successfully!")
        print(f"📊 Scraped {len(results)} hotels")
        print("\n💡 Note: In production, this data is passed directly to LLM for analysis")
        print("   (pros, cons, and recommendations)")
    else:
        print("\n⚠️  No results found.")

if __name__ == "__main__":
    main()
