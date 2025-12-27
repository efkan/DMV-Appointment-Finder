from datetime import datetime
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import SELECTORS, DMV_URL
from .core import random_delay, human_type

# ============================================================================
# EPIC-2: LOGIN FLOW
# ============================================================================

def perform_login(driver: webdriver.Chrome, params: dict) -> bool:
    """Perform the login flow on DMV website."""
    print("🔐 Starting login flow...")
    
    try:
        # Navigate to DMV page
        driver.get(DMV_URL)
        random_delay(3, 5)
        
        wait = WebDriverWait(driver, 15)
        
        # Action 1: Click appointment type
        print("  → Clicking appointment type...")
        appt_type = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["appointment_type"])))
        appt_type.click()
        random_delay()
        
        # Action 2: Input Permit Number
        print("  → Entering permit number...")
        permit_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["permit_number"])))
        human_type(permit_input, params["permit_number"])
        random_delay(1, 2)
        
        # Action 3: Input DOB
        print("  → Entering date of birth...")
        dob_input = driver.find_element(By.CSS_SELECTOR, SELECTORS["dob"])
        human_type(dob_input, params["dob"])
        random_delay(1, 2)
        
        # Action 4: Click Submit
        print("  → Submitting form...")
        submit_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS["submit_btn"])
        submit_btn.click()
        random_delay(3, 5)
        
        print("✅ Login flow completed!")
        return True
        
    except TimeoutException as e:
        print(f"❌ Login failed: Timeout waiting for element - {e}")
        return False
    except NoSuchElementException as e:
        print(f"❌ Login failed: Element not found - {e}")
        return False


# ============================================================================
# EPIC-3: OFFICE SEARCH
# ============================================================================

def verify_office_page(driver: webdriver.Chrome) -> bool:
    """Verify we're on the office selection page."""
    print("🔍 Verifying office selection page...")
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Which office would you like to visit?')]"))
        )
        print("✅ Office selection page verified!")
        return True
    except TimeoutException:
        print("❌ ALERT: 'Which office would you like to visit?' text NOT found!")
        return False


def search_office(driver: webdriver.Chrome, zip_code: str) -> bool:
    """Search for offices near a zip code."""
    print(f"🔎 Searching offices near zip code: {zip_code}")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Input zip code
        zip_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["zip_input"])))
        zip_input.clear()
        random_delay(0.5, 1)
        human_type(zip_input, zip_code)
        random_delay(1, 2)
        
        # Click search
        search_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS["search_btn"])
        search_btn.click()
        random_delay(2, 4)
        
        return True
        
    except Exception as e:
        print(f"❌ Office search failed: {e}")
        return False


# ============================================================================
# EPIC-4: OFFICE SELECTION
# ============================================================================

def select_first_office(driver: webdriver.Chrome) -> bool:
    """Select the first office in the result list."""
    print("🏢 Selecting first office...")
    
    try:
        wait = WebDriverWait(driver, 10)
        first_office_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["first_office"])))
        first_office_btn.click()
        random_delay(3, 5)
        print("✅ First office selected!")
        return True
        
    except Exception as e:
        print(f"❌ Office selection failed: {e}")
        return False


# ============================================================================
# EPIC-5: DATE COMPARISON LOGIC
# ============================================================================

def parse_calendar_date(driver: webdriver.Chrome) -> Optional[str]:
    """
    Read the calendar using specific selectors to find 'Open Times' and parse the date.
    Selector path: #appointments__date-cal ... .rbc-row-content > div
    Target: div.rbc-row-segment > span.rbc-event-available ("Open Times")
    Sibling: span.rbc-event-day-num--mobile (Date text: "Month Day, Year")
    """
    print("📅 Reading calendar...")
    
    # CRITICAL: Verify we're on the calendar page before attempting to parse
    current_url = driver.current_url
    if "appointments/select-date" not in current_url:
        print(f"  ❌ ERROR: Not on calendar page! Current URL: {current_url}")
        print(f"  Expected URL to contain: 'appointments/select-date'")
        return None
    
    try:
        wait = WebDriverWait(driver, 5) # Short wait
        
        # 1. Wait for at least one segment to appear to ensure calendar is loaded
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".rbc-row-segment")))
        except TimeoutException:
            print("  ⚠ No calendar rows found (timeout). Saving HTML for debug...")
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("  📂 Full page HTML saved to 'debug_page_source.html'")
            return None

        # 2. Find all row segments
        row_segments = driver.find_elements(By.CSS_SELECTOR, ".rbc-row-segment")
        print(f"  → Found {len(row_segments)} calendar segments. Checking each...")
        
        for i, segment in enumerate(row_segments):
            try:
                # Check for "Open Times" availability
                # We look for a child span with class "rbc-event-available"
                open_times_span = segment.find_elements(By.CSS_SELECTOR, "span.rbc-event-available")
                
                # Check text content robustly (handle hidden or whitespace)
                if open_times_span:
                    text_content = open_times_span[0].get_attribute("textContent").strip()
                    # print(f"    Segment {i}: Found status '{text_content}'") # verbose debug
                    
                    if text_content in ["Open Times", "Nearby Office Times"]:
                        print(f"  ✨ Found '{text_content}' slot at segment {i}!")
                        
                        # DEBUG: Log the HTML parsing context
                        try:
                            html_content = segment.get_attribute('outerHTML')
                            print(f"  🔍 HTML Context: {html_content}")
                        except Exception:
                            pass
                        
                        # Found a slot! Now find the date.
                        date_span = segment.find_elements(By.CSS_SELECTOR, "span.rbc-event-day-num--mobile")
                        if date_span:
                            # Use textContent because the element might be hidden on desktop view
                            date_text = date_span[0].get_attribute("textContent").strip()
                            print(f"  → Date text found: '{date_text}'")
                            
                            # Convert to MM/DD/YYYY
                            try:
                                date_obj = datetime.strptime(date_text, "%B %d, %Y")
                                formatted_date = date_obj.strftime("%m/%d/%Y")
                                print(f"  → Parsed date: {formatted_date}")
                                return formatted_date
                            except ValueError as ve:
                                print(f"  ❌ Date parsing error for '{date_text}': {ve}")
                                # CONTINUE searching! Do not return None.
                        else:
                            print("  ⚠ 'Open Times' found but NO date span sibling?")
            
            except Exception as inner_e:
                print(f"  ⚠ Error checking segment {i}: {inner_e}")
                continue
        
        print("  ⚠ No valid 'Open Times' slots found after checking all segments.")
        return None
            
    except Exception as e:
        print(f"❌ Calendar parsing failed: {e}")
        return None


def click_back_reset(driver: webdriver.Chrome) -> bool:
    """Click the back/reset button to return to office search."""
    print("🔙 Going back to office search...")
    
    try:
        wait = WebDriverWait(driver, 10)
        # Try to find the button
        back_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["back_btn"])))
        
        # In headless, complex interactions (hover, scroll) sometimes crash chrome on specific sites.
        # We will try a robust JS click directly.
        try:
            driver.execute_script("arguments[0].click();", back_btn)
        except Exception:
            # Fallback: try standard click
             back_btn.click()
            
        random_delay(2, 4)
        print("✅ Returned to office search!")
        return True
        
    except Exception as e:
        print(f"❌ Back/reset failed: {e}")
        # Don't return False immediately if we suspect the driver crashed, let the exception bubble up later
        # But here we just log.
        return False
