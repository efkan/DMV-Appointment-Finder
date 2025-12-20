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
    
    try:
        wait = WebDriverWait(driver, 5) # Short wait as we might not always find slots
        
        # Base container for date rows
        # The user specified: #appointments__date-cal > div > div > div.rbc-month-view > div:nth-child(2) > div.rbc-row-content > div
        # We'll use a slightly more generic css to find all row segments in the calendar grid
        # because "div:nth-child(2)" might only select one specific week/row.
        # We want to scan the whole month view.
        
        # Finding all row segments that might contain events
        # "div.rbc-row-segment" is the container for a day cell implementation in this grid
        row_segments = driver.find_elements(By.CSS_SELECTOR, ".rbc-row-segment")
        
        for segment in row_segments:
            try:
                # Check for "Open Times" availability
                # We look for a child span with class "rbc-event-available"
                open_times_span = segment.find_elements(By.CSS_SELECTOR, "span.rbc-event-available")
                
                if open_times_span and open_times_span[0].text.strip() == "Open Times":
                    print("  ✨ Found 'Open Times' slot!")
                    
                    # DEBUG: Log the HTML parsing context
                    try:
                        html_content = segment.get_attribute('outerHTML')
                        print(f"  🔍 HTML Context: {html_content}")
                    except Exception as html_e:
                        print(f"  ⚠ Could not log HTML: {html_e}")
                    
                    # Found a slot! Now find the date.
                    # The user said the date is in a sibling span with class "rbc-event-day-num--mobile"
                    # However, siblings in Selenium often require xpath or finding parent then child.
                    # Assuming they are siblings within the same parent `segment`? 
                    # If they are siblings, we can find them relative to the segment.
                    
                    date_span = segment.find_elements(By.CSS_SELECTOR, "span.rbc-event-day-num--mobile")
                    if date_span:
                        # Use textContent because the element might be hidden on desktop view (Selenium .text returns empty for hidden nodes)
                        date_text = date_span[0].get_attribute("textContent").strip() # e.g. "January 7, 2026"
                        print(f"  → Date text found: '{date_text}'")
                        
                        # Convert to MM/DD/YYYY
                        try:
                            date_obj = datetime.strptime(date_text, "%B %d, %Y")
                            formatted_date = date_obj.strftime("%m/%d/%Y")
                            print(f"  → Parsed date: {formatted_date}")
                            return formatted_date
                        except ValueError as ve:
                            print(f"  ❌ Date parsing error for '{date_text}': {ve}")
            
            except Exception as inner_e:
                # Continue searching other segments even if one fails
                continue
        
        print("  ⚠ No 'Open Times' found on current calendar view")
        return None
            
    except Exception as e:
        print(f"❌ Calendar parsing failed: {e}")
        return None


def click_back_reset(driver: webdriver.Chrome) -> bool:
    """Click the back/reset button to return to office search."""
    print("🔙 Going back to office search...")
    
    try:
        wait = WebDriverWait(driver, 10)
        back_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["back_btn"])))
        back_btn.click()
        random_delay(2, 4)
        print("✅ Returned to office search!")
        return True
        
    except Exception as e:
        print(f"❌ Back/reset failed: {e}")
        return False
