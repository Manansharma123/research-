from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import csv
import re

def setup_driver(headless=True):
    """Setup Chrome driver in headless mode by default"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1920,1080')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    
    return driver

def wait_for_page_ready(driver, timeout=10):
    """Wait for page to load"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)
        return True
    except:
        return False

def wait_for_autocomplete(driver, timeout=10):
    """Wait for Edustoke's location dropdown to appear"""
    print("   Waiting for autocomplete dropdown...")
    
    autocomplete_selectors = [
        ".loc-dropdown",
        ".dropdown-item",
        "div.loc-dropdown button"
    ]
    
    for selector in autocomplete_selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            print(f"   ✅ Autocomplete appeared (found: {selector})")
            
            try:
                items = driver.find_elements(By.CSS_SELECTOR, ".dropdown-item")
                if items:
                    print(f"   📋 Dropdown has {len(items)} items:")
                    for i, item in enumerate(items[:3], 1):
                        text = item.text.strip()
                        if text:
                            print(f"      {i}. {text[:60]}")
            except:
                pass
            
            return True
        except:
            continue
    
    print("   ⚠️  Autocomplete not detected")
    return False

def select_first_autocomplete_option(driver, location_input):
    """Select the first option from Edustoke's location dropdown"""
    print("🔍 Step 3: Selecting from autocomplete dropdown...")
    
    time.sleep(2)
    
    # METHOD 1: Click first .dropdown-item button
    try:
        print("   Method 1: Clicking .dropdown-item button...")
        
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".loc-dropdown"))
        )
        print("   ✅ Dropdown container visible")
        
        buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dropdown-item"))
        )
        
        if buttons:
            first_button = buttons[0]
            print(f"   Found {len(buttons)} location options")
            
            button_text = first_button.text.strip()
            print(f"   Selecting: {button_text[:60]}")
            
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".dropdown-item"))
            )
            time.sleep(0.5)
            
            try:
                first_button.click()
                print("   ✅ Clicked first location!")
                time.sleep(2)
                return True
            except:
                driver.execute_script("arguments[0].click();", first_button)
                print("   ✅ JS clicked first location!")
                time.sleep(2)
                return True
                
    except Exception as e:
        print(f"   Method 1 failed: {str(e)[:80]}")
    
    # METHOD 2: Use data-place-id selector
    try:
        print("   Method 2: Using data-place-id selector...")
        
        buttons = driver.find_elements(By.CSS_SELECTOR, "button.dropdown-item[data-place-id]")
        
        if buttons:
            first = buttons[0]
            place_id = first.get_attribute('data-place-id')
            print(f"   Found button with place_id: {place_id[:20]}...")
            
            driver.execute_script("arguments[0].click();", first)
            print("   ✅ Clicked via data-place-id!")
            time.sleep(2)
            return True
            
    except Exception as e:
        print(f"   Method 2 failed: {str(e)[:80]}")
    
    # METHOD 3: Click inside .loc-dropdown div
    try:
        print("   Method 3: Finding button inside .loc-dropdown...")
        
        dropdown = driver.find_element(By.CSS_SELECTOR, ".loc-dropdown")
        buttons = dropdown.find_elements(By.TAG_NAME, "button")
        
        if buttons:
            print(f"   Found {len(buttons)} buttons in dropdown")
            driver.execute_script("arguments[0].click();", buttons[0])
            print("   ✅ Clicked first button in dropdown!")
            time.sleep(2)
            return True
            
    except Exception as e:
        print(f"   Method 3 failed: {str(e)[:80]}")
    
    # METHOD 4: Arrow key navigation
    try:
        print("   Method 4: Keyboard navigation (Arrow Down + Enter)...")
        
        location_input.click()
        time.sleep(0.5)
        
        location_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        
        location_input.send_keys(Keys.ENTER)
        print("   ✅ Selected via Arrow Down + Enter!")
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"   Method 4 failed: {str(e)[:80]}")
    
    # METHOD 5: Try clicking by button class chain
    try:
        print("   Method 5: CSS selector chain...")
        
        first_btn = driver.find_element(By.CSS_SELECTOR, 
            "div.loc-dropdown button.dropdown-item.px-3.c-auto-comp-item")
        
        driver.execute_script("arguments[0].click();", first_btn)
        print("   ✅ Clicked via full CSS chain!")
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"   Method 5 failed: {str(e)[:80]}")
    
    print("   ⚠️  All methods failed, proceeding anyway...")
    return False

def search_edustoke(driver, location, school_category="Day School"):
    """Search on Edustoke"""
    print(f"\n{'='*70}")
    print(f"🔍 EDUSTOKE SEARCH")
    print(f"{'='*70}")
    print(f"📍 Location: {location}")
    print(f"🏫 Category: {school_category}\n")
    
    try:
        print("🌐 Loading homepage...")
        driver.get("https://www.edustoke.com")
        wait_for_page_ready(driver)
        print(f"✅ Page loaded\n")
        
        # STEP 1: SELECT CATEGORY
        print("📚 Step 1: Selecting category...")
        
        try:
            category_btn = None
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            
            for btn in buttons:
                btn_text = btn.text.strip()
                if 'select' in btn_text.lower() or 'category' in btn_text.lower() or 'school' in btn_text.lower():
                    category_btn = btn
                    print(f"   ✅ Found category button: '{btn_text}'")
                    break
            
            if category_btn:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_btn)
                time.sleep(1)
                category_btn.click()
                time.sleep(2)
                
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='option'], li, a"))
                )
                time.sleep(1)
                
                options = driver.find_elements(By.CSS_SELECTOR, "div[role='option'], .option, li, a")
                
                for opt in options:
                    opt_text = opt.text.strip()
                    if school_category.lower() in opt_text.lower():
                        print(f"   ✅ Clicking: '{opt_text}'")
                        driver.execute_script("arguments[0].click();", opt)
                        time.sleep(2)
                        break
        except Exception as e:
            print(f"   ⚠️  Category selection error: {str(e)[:60]}\n")
        
        print()
        
        # STEP 2: FILL LOCATION
        print("📝 Step 2: Filling location field...")
        
        location_input = None
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"   Found {len(inputs)} input fields")
        
        for inp in inputs:
            try:
                if not inp.is_displayed():
                    continue
                
                placeholder = inp.get_attribute('placeholder') or ''
                
                if any(kw in placeholder.lower() for kw in ['location', 'school name', 'search']):
                    location_input = inp
                    print(f"   ✅ Found location input (placeholder: '{placeholder}')\n")
                    break
            except:
                continue
        
        if not location_input:
            visible = [i for i in inputs if i.is_displayed()]
            if len(visible) >= 2:
                location_input = visible[-1]
                print(f"   Using last visible input\n")
        
        if not location_input:
            print("   ❌ Could not find location input\n")
            return False
        
        print(f"📝 Entering location: '{location}'")
        
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", location_input)
            time.sleep(1)
            
            location_input.click()
            time.sleep(0.5)
            location_input.send_keys(Keys.CONTROL + 'a')
            location_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            for char in location:
                location_input.send_keys(char)
                time.sleep(0.1)
            
            print(f"   ✅ Location entered: '{location_input.get_attribute('value')}'")
            
        except Exception as e:
            print(f"   ❌ Error filling location: {str(e)}\n")
            return False
        
        print()
        
        # STEP 3: AUTOCOMPLETE
        wait_for_autocomplete(driver, timeout=8)
        success = select_first_autocomplete_option(driver, location_input)
        
        print()
        
        # STEP 4: SEARCH BUTTON
        print("🔎 Step 4: Clicking search button...\n")
        
        search_found = False
        
        search_selectors = [
            "button[type='submit']",
            "button.search",
            "button[aria-label*='search' i]",
            "button[class*='search' i]"
        ]
        
        for selector in search_selectors:
            try:
                search_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if search_btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
                    time.sleep(1)
                    
                    try:
                        search_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", search_btn)
                    
                    print(f"   ✅ Search button clicked! (selector: {selector})")
                    search_found = True
                    time.sleep(5)
                    break
            except:
                continue
        
        if not search_found:
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                try:
                    if not btn.is_displayed():
                        continue
                    
                    btn_html = btn.get_attribute('outerHTML').lower()
                    if any(kw in btn_html for kw in ['search', 'submit']):
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        btn.click()
                        print(f"   ✅ Search button clicked!")
                        search_found = True
                        time.sleep(5)
                        break
                except:
                    continue
        
        if not search_found:
            print(f"   ⚠️  Search button not found, trying Enter key...")
            location_input.send_keys(Keys.ENTER)
            time.sleep(5)
        
        print()
        
        # STEP 5: VERIFY
        print("⏳ Verifying results...")
        time.sleep(3)
        
        current_url = driver.current_url
        print(f"   URL: {current_url}")
        print(f"   Title: {driver.title}\n")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class*='card'], article"))
            )
            print(f"   ✅ School cards loaded\n")
            return True
        except:
            print(f"   ⚠️  Waiting for cards...\n")
            time.sleep(3)
            return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def scroll_and_load(driver, max_scrolls=15):
    """Scroll to load all content"""
    print("📜 Scrolling to load schools...\n")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print(f"   Reached bottom")
            break
        
        last_height = new_height
        scrolls += 1
        print(f"   Scroll {scrolls}")
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    print("✅ Scrolling complete\n")

def scrape_schools(driver):
    """Scrape school data with duplicate removal"""
    print("🎯 Extracting schools...\n")
    
    schools = []
    seen_schools = set()
    
    card_selectors = [
        "div[class*='SchoolCard']",
        "div[class*='school-card']",
        "div.school-item",
        "a[href*='/school']",
        "article[class*='school']",
        "div.card",
        "article"
    ]
    
    school_elements = []
    
    for selector in card_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            valid = [e for e in elements if len(e.text.strip()) > 50]
            if len(valid) > 2:
                school_elements = valid
                print(f"✅ Found {len(school_elements)} school cards (before deduplication)\n")
                break
        except:
            continue
    
    if not school_elements:
        print("⚠️  No schools found\n")
        return []
    
    processed = 0
    for idx, card in enumerate(school_elements, 1):
        try:
            data = extract_card_data(card, idx)
            
            if data.get('school_name'):
                unique_key = (
                    data.get('school_name', '').lower().strip(),
                    data.get('fees', '') or str(idx)
                )
                
                if unique_key in seen_schools:
                    continue
                
                seen_schools.add(unique_key)
                processed += 1
                
                data['index'] = processed
                
                schools.append(data)
                print(f"✓ {processed}. {data['school_name']}")
                if data.get('rating'):
                    print(f"   ⭐ Rating: {data['rating']}")
                if data.get('fees'):
                    print(f"   💰 {data['fees']}")
                if data.get('board'):
                    print(f"   📚 Board: {data['board']}")
                if data.get('grade'):
                    print(f"   🎓 Grade: {data['grade']}")
        except Exception as e:
            pass
    
    print(f"\n📊 Extracted {len(schools)} unique schools from {len(school_elements)} elements")
    print()
    return schools

def extract_card_data(card, index):
    """Extract school data from card - ONLY rating, fees, board, grade"""
    data = {
        'index': index,
        'school_name': None,
        'rating': None,
        'fees': None,
        'board': None,
        'grade': None
    }
    
    try:
        full_text = card.text
        
        # School name
        for tag in ['h2', 'h3', 'h4', 'h1']:
            try:
                name_elem = card.find_element(By.TAG_NAME, tag)
                name = name_elem.text.strip()
                if name and len(name) > 3:
                    data['school_name'] = name
                    break
            except:
                continue
        
        if not data['school_name']:
            try:
                link = card.find_element(By.TAG_NAME, 'a')
                data['school_name'] = link.text.strip()
            except:
                pass
        
        # Fees
        fee_match = re.search(r'₹\s*([\d,]+)\s*/\s*annum', full_text)
        if fee_match:
            data['fees'] = '₹' + fee_match.group(1) + ' / annum'
        else:
            fee_match = re.search(r'₹\s*([\d,]+)', full_text)
            if fee_match:
                data['fees'] = '₹' + fee_match.group(1)
        
        # ============ ENHANCED RATING EXTRACTION ============
        # Priority 1: Look for <span class="rating"> (Edustoke specific)
        try:
            rating_span = card.find_element(By.CSS_SELECTOR, 'span.rating')
            rating_text = rating_span.text.strip()
            rating_num = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_num:
                potential_rating = rating_num.group(1)
                if 0 <= float(potential_rating) <= 5:
                    data['rating'] = potential_rating
        except:
            pass
        
        # Priority 2: Look for rating in review container
        if not data['rating']:
            try:
                review_containers = card.find_elements(By.CSS_SELECTOR, 
                    '[class*="rating-review"], [class*="review"], [class*="rating"]')
                for container in review_containers:
                    container_text = container.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', container_text)
                    if rating_match:
                        potential_rating = rating_match.group(1)
                        try:
                            if 0 <= float(potential_rating) <= 5:
                                data['rating'] = potential_rating
                                break
                        except ValueError:
                            continue
            except:
                pass
        
        # Priority 3: Search full text with patterns
        if not data['rating']:
            rating_patterns = [
                r'rating["\s:]*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*(?:★|⭐|stars?)',
                r'(\d+\.?\d*)\s*/\s*5',
                r'(\d+\.?\d*)\s*out of 5',
            ]
            
            for pattern in rating_patterns:
                rating_match = re.search(pattern, full_text, re.IGNORECASE)
                if rating_match:
                    potential_rating = rating_match.group(1)
                    try:
                        if 0 <= float(potential_rating) <= 5:
                            data['rating'] = potential_rating
                            break
                    except ValueError:
                        continue
        
        # ============ ENHANCED BOARD EXTRACTION (Edustoke Specific) ============
        # Method 1: Find the feature-wrapper div that contains "Board" label
        try:
            feature_divs = card.find_elements(By.CSS_SELECTOR, '.feature-wrapper, [class*="feature"]')
            for div in feature_divs:
                div_text = div.text.strip()
                if div_text.startswith('Board\n') or 'Board' in div_text.split('\n')[0]:
                    try:
                        bold_span = div.find_element(By.CSS_SELECTOR, '.font-weight-bold, span.font-weight-bold')
                        board_value = bold_span.text.strip()
                        if board_value and board_value != 'Board':
                            data['board'] = board_value
                            break
                    except:
                        lines = div_text.split('\n')
                        if len(lines) >= 2 and lines[0].strip() == 'Board':
                            data['board'] = lines[1].strip()
                            break
        except:
            pass
        
        # Method 2: Look for pattern "Board\nCBSE" in card text
        if not data['board']:
            board_match = re.search(r'Board\s*\n\s*([A-Z][A-Z\s]+)', full_text)
            if board_match:
                potential_board = board_match.group(1).strip()
                if len(potential_board) <= 20:
                    data['board'] = potential_board
        
        # Method 3: Search for common board keywords in full text
        if not data['board']:
            board_keywords = [
                'CBSE', 'ICSE', 'IB', 'IGCSE', 'ISC',
                'State Board', 'SSC', 'NIOS',
                'Cambridge', 'Maharashtra Board', 'CISCE'
            ]
            for board in board_keywords:
                if board in full_text:
                    data['board'] = board
                    break
        
        # ============ GRADE EXTRACTION ============
        try:
            feature_divs = card.find_elements(By.CSS_SELECTOR, '.feature-wrapper, [class*="feature"]')
            for div in feature_divs:
                div_text = div.text.strip()
                if div_text.startswith('Grade\n') or 'Grade' in div_text.split('\n')[0]:
                    try:
                        bold_span = div.find_element(By.CSS_SELECTOR, '.font-weight-bold, span.font-weight-bold')
                        grade_value = bold_span.text.strip()
                        if grade_value and grade_value != 'Grade':
                            data['grade'] = grade_value
                            break
                    except:
                        lines = div_text.split('\n')
                        if len(lines) >= 2 and lines[0].strip() == 'Grade':
                            data['grade'] = lines[1].strip()
                            break
        except:
            pass
        
        if not data['grade']:
            grade_match = re.search(r'Grade\s*\n\s*([^\n]+)', full_text)
            if grade_match:
                data['grade'] = grade_match.group(1).strip()
            else:
                grade_match = re.search(r'(Nursery|KG|Primary|Secondary)\s*-?\s*(\d+)?', full_text)
                if grade_match:
                    data['grade'] = grade_match.group(0)
        
    except Exception as e:
        pass
    
    return data

def save_data(schools, location):
    """Save to CSV and JSON"""
    if not schools:
        return
    
    clean_loc = re.sub(r'[^\w\s-]', '', location).strip().replace(' ', '_')
    csv_file = f"schools_{clean_loc}.csv"
    json_file = f"schools_{clean_loc}.json"
    
    # CSV
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(schools[0].keys()))
            writer.writeheader()
            writer.writerows(schools)
        print(f"💾 Saved: {csv_file}")
    except Exception as e:
        print(f"Error saving CSV: {str(e)}")
    
    # JSON
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(schools, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved: {json_file}")
    except Exception as e:
        print(f"Error saving JSON: {str(e)}")
    
    # Stats
    total = len(schools)
    with_fees = sum(1 for s in schools if s.get('fees'))
    with_rating = sum(1 for s in schools if s.get('rating'))
    with_board = sum(1 for s in schools if s.get('board'))
    with_grade = sum(1 for s in schools if s.get('grade'))
    
    print(f"\n📊 Statistics:")
    print(f"   Total Schools: {total}")
    print(f"   With Fees: {with_fees} ({100*with_fees//total if total else 0}%)")
    print(f"   With Rating: {with_rating} ({100*with_rating//total if total else 0}%)")
    print(f"   With Board: {with_board} ({100*with_board//total if total else 0}%)")
    print(f"   With Grade: {with_grade} ({100*with_grade//total if total else 0}%)")

def main():
    """Main function - runs in headless mode with Day School as default"""
    print("="*70)
    print("🏫 EDUSTOKE SCRAPER - Headless Mode")
    print("="*70)
    
    location = input("\n📍 Enter location: ").strip() or "Zirakpur, Mohali"
    print(f"\n🎯 Searching for: {location}")
    print(f"🏫 Category: Day School (default)")
    print(f"🖥️  Mode: Headless (background)")
    
    school_category = "Day School"
    
    driver = None
    try:
        print("\n🚀 Starting browser in headless mode...")
        driver = setup_driver(headless=True)
        
        if search_edustoke(driver, location, school_category):
            scroll_and_load(driver)
            schools = scrape_schools(driver)
            
            if schools:
                print(f"\n{'='*70}")
                print(f"🎉 SUCCESS: Found {len(schools)} schools!")
                print(f"{'='*70}\n")
                
                save_data(schools, location)
                
                print(f"\n📋 Sample School Data:")
                print(json.dumps(schools[0], indent=2, ensure_ascii=False))
                
                complete = [s for s in schools if all([s.get('rating'), s.get('fees'), s.get('board'), s.get('grade')])]
                print(f"\n✅ Schools with complete data: {len(complete)}/{len(schools)}")
            else:
                print("\n⚠️  No schools extracted")
        else:
            print("\n❌ Search failed")
            
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    main()