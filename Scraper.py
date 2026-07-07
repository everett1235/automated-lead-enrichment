"""
GOOGLE MAPS SCRAPER - CUSTOM FORMATTED OUTPUT
Formats CSV exactly how you want it with split address fields
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import re

# ========== SETTINGS ==========
CITY_OR_ZIP = "Gibsonia, PA"  # Your target location
CATEGORY = "Automotive"  # Business type
RESULTS_LIMIT = 50  # How many businesses WITHOUT websites you want
SCROLL_PAUSE = 2  # Seconds to wait between scrolls
DEBUG_MODE = False  # Set to True to see ALL businesses

# ========== SCRAPER CLASS ==========
class GoogleMapsScraper:
    def __init__(self, debug=False):
        self.driver = None
        self.businesses_no_website = []
        self.all_businesses = []
        self.debug = debug
        self.search_category = ""
        
    def setup_driver(self):
        """Initialize Chrome driver with geolocation DISABLED"""
        print("Setting up Chrome browser...")
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # DISABLE GEOLOCATION
        prefs = {
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument('--disable-geolocation')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        print("✓ Browser ready!\n")
        
    def parse_address(self, full_address):
        """Split address into street, city, state, zip"""
        if not full_address or full_address == "N/A":
            return {
                'Street': 'N/A',
                'City': 'N/A',
                'State': 'N/A',
                'Zip': 'N/A'
            }
        
        try:
            # Address format is usually: "123 Main St, City, ST 12345"
            parts = [p.strip() for p in full_address.split(',')]
            
            if len(parts) >= 3:
                street = parts[0]
                city = parts[1]
                
                # Last part usually has "STATE ZIP"
                state_zip = parts[2].strip().split()
                state = state_zip[0] if len(state_zip) > 0 else 'N/A'
                zip_code = state_zip[1] if len(state_zip) > 1 else 'N/A'
                
                return {
                    'Street': street,
                    'City': city,
                    'State': state,
                    'Zip': zip_code
                }
            elif len(parts) == 2:
                # Just street and city/state
                return {
                    'Street': parts[0],
                    'City': parts[1],
                    'State': 'N/A',
                    'Zip': 'N/A'
                }
            else:
                return {
                    'Street': full_address,
                    'City': 'N/A',
                    'State': 'N/A',
                    'Zip': 'N/A'
                }
        except:
            return {
                'Street': full_address,
                'City': 'N/A',
                'State': 'N/A',
                'Zip': 'N/A'
            }
    
    def search_google_maps(self, location, category):
        """Search for businesses on Google Maps"""
        self.search_category = category  # Store for later
        search_query = f"{category} in {location}"
        print(f"Searching: {search_query}")
        
        from urllib.parse import quote_plus
        encoded_query = quote_plus(search_query)
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        
        print(f"Opening: {search_url}")
        self.driver.get(search_url)
        
        print("Waiting for results to load...")
        time.sleep(6)
        
        try:
            current_url = self.driver.current_url
            print(f"✓ URL loaded\n")
        except:
            pass
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )
            print("✓ Results loaded!\n")
        except TimeoutException:
            print("⚠️  Results may not have loaded properly, but continuing...\n")
        
    def scroll_results_panel(self):
        """Scroll the results panel to load more businesses"""
        print("Loading more results by scrolling...")
        
        try:
            results_panel = None
            selectors = [
                '//div[@role="feed"]',
                '//div[contains(@class, "m6QErb")]',
            ]
            
            for selector in selectors:
                try:
                    results_panel = self.driver.find_element(By.XPATH, selector)
                    print(f"✓ Found results panel")
                    break
                except:
                    continue
            
            if not results_panel:
                print("⚠️  Could not find scrollable panel")
                return
            
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", results_panel)
            
            for i in range(10):
                self.driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    results_panel
                )
                time.sleep(SCROLL_PAUSE)
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", results_panel)
                if new_height == last_height:
                    print(f"  Reached end at scroll {i+1}")
                    break
                last_height = new_height
                print(f"  Scroll {i+1}/10...")
                
        except Exception as e:
            print(f"⚠️  Scroll error: {e}")
            
    def extract_businesses(self, limit):
        """Extract business information from search results"""
        print("\nExtracting business data...\n")
        print("-" * 70)
        
        total_checked = 0
        
        try:
            time.sleep(3)
            
            business_elements = []
            selectors = [
                'a[href*="/maps/place/"]',
                'div.Nv2PK a',
                'a.hfpxzc',
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        business_elements = elements
                        print(f"✓ Found {len(business_elements)} businesses\n")
                        break
                except:
                    continue
            
            if not business_elements:
                print("❌ Could not find any business listings!")
                return
            
            for idx, element in enumerate(business_elements):
                if not self.debug and len(self.businesses_no_website) >= limit:
                    print(f"\n✓ Reached target of {limit} businesses!")
                    break
                    
                try:
                    total_checked += 1
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                    
                    # Click
                    try:
                        element.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    time.sleep(random.uniform(2.5, 3.5))
                    
                    # Extract details
                    business_data = self.extract_business_details()
                    
                    if business_data and business_data['Name'] != 'N/A':
                        name = business_data['Name']
                        website_status = business_data['Website']
                        has_website = website_status not in ['No website listed', 'No website found', 'N/A']
                        
                        # Parse address into components
                        address_parts = self.parse_address(business_data['Address'])
                        
                        # Only save if NO website
                        if not has_website:
                            formatted_business = {
                                'Business Name': name,
                                'Category': self.search_category,
                                'Website Status': 'No Website',
                                'Street Address': address_parts['Street'],
                                'City': address_parts['City'],
                                'State': address_parts['State'],
                                'Zip Code': address_parts['Zip'],
                                'Reviews': business_data.get('Reviews', 'N/A'),
                                'Rating': business_data.get('Rating', 'N/A'),
                                'Phone': business_data['Phone']
                            }
                            
                            self.businesses_no_website.append(formatted_business)
                            
                            print(f"✓ [{len(self.businesses_no_website)}] {name[:50]}")
                            print(f"   📍 {address_parts['Street']}, {address_parts['City']}, {address_parts['State']} {address_parts['Zip']}")
                            print(f"   📞 {business_data['Phone']}")
                            print(f"   🌐 NO WEBSITE\n")
                        else:
                            print(f"✗ Skipped: {name[:50]} (has website)\n")
                    
                except KeyboardInterrupt:
                    print("\n⚠️  Stopping...")
                    break
                except Exception as e:
                    print(f"⚠️  Error #{total_checked}: {str(e)[:80]}\n")
                    try:
                        self.driver.back()
                        time.sleep(1)
                    except:
                        pass
                    continue
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 70)
        print(f"\nTotal checked: {total_checked}")
        print(f"Businesses WITHOUT websites found: {len(self.businesses_no_website)}")
        
    def extract_business_details(self):
        """Extract details with reviews and ratings"""
        try:
            time.sleep(1.5)
            
            # Name
            name = "N/A"
            name_selectors = [
                'h1.DUwDvf',
                'h1[class*="fontHeadlineLarge"]',
                'h1',
            ]
            for selector in name_selectors:
                try:
                    name = self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                    if name:
                        break
                except:
                    continue
            
            # Address
            address = "N/A"
            address_selectors = [
                'button[data-item-id="address"]',
                'button[aria-label*="Address"]',
                'div[data-item-id="address"]',
            ]
            for selector in address_selectors:
                try:
                    address = self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                    if address:
                        break
                except:
                    continue
            
            # Phone
            phone = "N/A"
            phone_selectors = [
                'button[data-item-id^="phone"]',
                'button[aria-label*="Phone"]',
            ]
            for selector in phone_selectors:
                try:
                    phone = self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                    if phone:
                        break
                except:
                    continue
            
            # Rating
            rating = "N/A"
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, 'span[aria-hidden="true"]')
                rating_text = rating_elem.text.strip()
                # Extract number (e.g., "4.5" from "4.5★")
                if rating_text:
                    rating = rating_text.replace('★', '').strip()
            except:
                pass
            
            # Reviews count
            reviews = "N/A"
            try:
                # Look for review count (e.g., "(123)")
                review_selectors = [
                    'button[aria-label*="reviews"]',
                    'span[aria-label*="reviews"]',
                ]
                for selector in review_selectors:
                    try:
                        review_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        review_text = review_elem.text.strip()
                        # Extract number from "(123)" or "123 reviews"
                        numbers = re.findall(r'\d+', review_text)
                        if numbers:
                            reviews = numbers[0]
                            break
                    except:
                        continue
            except:
                pass
            
            # Website detection
            website = "No website listed"
            
            website_selectors = [
                'a[data-item-id="authority"]',
                'a[data-item-id*="website"]',
                'a[aria-label*="Website"]',
                'button[data-item-id="authority"]',
            ]
            
            for selector in website_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    href = elem.get_attribute('href')
                    if href and 'google.com' not in href and 'maps' not in href:
                        website = href
                        break
                except:
                    continue
            
            if website == "No website listed":
                try:
                    page_source = self.driver.page_source.lower()
                    website_indicators = [
                        'visit website',
                        'website:',
                        'data-item-id="authority"',
                    ]
                    has_website_indicator = any(indicator in page_source for indicator in website_indicators)
                    if not has_website_indicator:
                        website = "No website found"
                except:
                    pass
            
            return {
                'Name': name,
                'Address': address,
                'Phone': phone,
                'Rating': rating,
                'Reviews': reviews,
                'Website': website
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting: {e}")
            return None
    
    def scrape(self, location, category, limit):
        """Main scraping workflow"""
        try:
            self.setup_driver()
            self.search_google_maps(location, category)
            self.scroll_results_panel()
            self.extract_businesses(limit)
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            
        finally:
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()
        
        return self.businesses_no_website


# ========== MAIN EXECUTION ==========
def main():
    print("=" * 70)
    print("GOOGLE MAPS SCRAPER - CUSTOM FORMATTED OUTPUT")
    print("=" * 70)
    print()
    
    scraper = GoogleMapsScraper(debug=DEBUG_MODE)
    results = scraper.scrape(CITY_OR_ZIP, CATEGORY, RESULTS_LIMIT)
    
    if results:
        df = pd.DataFrame(results)
        
        # Ensure column order is exactly right
        column_order = [
            'Business Name',
            'Category',
            'Website Status',
            'Street Address',
            'City',
            'State',
            'Zip Code',
            'Reviews',
            'Rating',
            'Phone'
        ]
        df = df[column_order]
        
        save_path = "/Users/everettdenniston/Desktop/pythin/businesses_no_website_gmaps.csv"
        df.to_csv(save_path, index=False)
        
        print("\n" + "=" * 70)
        print(f"✓ SUCCESS!")
        print(f"✓ Found {len(results)} businesses WITHOUT websites")
        print(f"✓ Saved to: {save_path}")
        print("=" * 70)
        
        print("\n📊 PREVIEW OF FORMATTED OUTPUT:")
        print(df.head(5).to_string(index=False))
        
    else:
        print("\n⚠️  No businesses without websites found.")


if __name__ == "__main__":
    main()
