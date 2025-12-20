#!/usr/bin/env python3
"""
DMV Appointment Finder - California DMV Automation
Checks appointment slots and notifies via NTFY.sh when better dates are found.

Team:
- Product Manager: Atlas
- Senior Full-Stack Developer: Neo
- QA Engineer: Bugsy
"""

import time
import random
import re
import requests
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================================
# CONFIGURATION
# ============================================================================

DMV_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type"
NTFY_TOPIC = "dmv-appointment-finder"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
PARAMETERS_FILE = Path(__file__).parent / "Management" / "parameters.md"

# CSS Selectors
SELECTORS = {
    "appointment_type": "#appointment-type-selector > div > div:nth-child(2) > div > fieldset > ul > li:nth-child(1) > label > span:nth-child(1)",
    "permit_number": "#dlNumber",
    "dob": "#dob",
    "submit_btn": "#appointment-type-selector > div > div:nth-child(2) > div > div.button-holder > button",
    "zip_input": "#inputKeyWord",
    "search_btn": "#locations-search > button",
    "first_office": "#js-location-result-list > li:nth-child(1) > div > div.search-card__options > div > button",
    "calendar_label": "#rbc-toolbar-label",
    "back_btn": "#appointments-react-root > section > div.appointments__top-bar > div > div:nth-child(2) > a",
}


# ============================================================================
# HUMAN-LIKE BEHAVIOR
# ============================================================================

def random_delay(min_sec: float = 2.0, max_sec: float = 5.0) -> None:
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def human_type(element, text: str) -> None:
    """Type text character by character with random delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))


# ============================================================================
# PARAMETERS HANDLING
# ============================================================================

def read_parameters() -> dict:
    """Read parameters from parameters.md file."""
    params = {
        "zip_codes": [],
        "zip_codes_checked": [],
        "permit_number": "",
        "dob": "",
        "earliest_date": "",
        "earliest_zip": "",
    }
    
    content = PARAMETERS_FILE.read_text()
    
    # Parse zip codes
    zip_match = re.search(r"Zip Codes:\s*(.+)", content)
    if zip_match:
        zips = zip_match.group(1).strip()
        if zips:
            params["zip_codes"] = [z.strip() for z in zips.split(",") if z.strip()]
    
    # Parse checked zip codes
    checked_match = re.search(r"Zip Codes Checked:\s*(.+)?", content)
    if checked_match and checked_match.group(1):
        checked = checked_match.group(1).strip()
        if checked:
            params["zip_codes_checked"] = [z.strip() for z in checked.split(",") if z.strip()]
    
    # Parse permit number
    permit_match = re.search(r"Permit Number:\s*(\S+)", content)
    if permit_match:
        params["permit_number"] = permit_match.group(1).strip()
    
    # Parse DOB
    dob_match = re.search(r"Date of Birth:\s*(\S+)", content)
    if dob_match:
        params["dob"] = dob_match.group(1).strip()
    
    # Parse earliest availability
    earliest_zip_match = re.search(r"Found Earliest Availability Zip Code:\s*(\S+)?", content)
    if earliest_zip_match and earliest_zip_match.group(1):
        params["earliest_zip"] = earliest_zip_match.group(1).strip()
    
    earliest_date_match = re.search(r"Found Earliest Availability Date:\s*(\S+)?", content)
    if earliest_date_match and earliest_date_match.group(1):
        params["earliest_date"] = earliest_date_match.group(1).strip()
    
    return params


def update_parameters(zip_checked: str = None, new_date: str = None, new_zip: str = None) -> None:
    """Update parameters.md with checked zip codes and new earliest availability."""
    content = PARAMETERS_FILE.read_text()
    
    if zip_checked:
        # Add to checked zip codes
        checked_match = re.search(r"(Zip Codes Checked:)\s*(.*)?", content)
        if checked_match:
            existing = checked_match.group(2).strip() if checked_match.group(2) else ""
            if existing:
                new_checked = f"{existing}, {zip_checked}"
            else:
                new_checked = zip_checked
            content = re.sub(
                r"Zip Codes Checked:\s*.*",
                f"Zip Codes Checked: {new_checked}",
                content
            )
    
    if new_date:
        content = re.sub(
            r"Found Earliest Availability Date:\s*\S*",
            f"Found Earliest Availability Date: {new_date}",
            content
        )
    
    if new_zip:
        content = re.sub(
            r"Found Earliest Availability Zip Code:\s*\S*",
            f"Found Earliest Availability Zip Code: {new_zip}",
            content
        )
    
    PARAMETERS_FILE.write_text(content)


def get_unchecked_zip_codes(params: dict) -> list:
    """Get list of zip codes that haven't been checked yet."""
    all_zips = params["zip_codes"]
    checked = params["zip_codes_checked"]
    return [z for z in all_zips if z not in checked]


# ============================================================================
# BROWSER SETUP
# ============================================================================

def create_driver() -> webdriver.Chrome:
    """Create a simple Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


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
        
        # Update parameters - mark zip as checked
        update_parameters(zip_checked=zip_code)
        print(f"  ✓ Zip code {zip_code} marked as checked")
        
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

def parse_calendar_date(driver: webdriver.Chrome) -> str | None:
    """Read the calendar and find the earliest available date."""
    print("📅 Reading calendar...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Read month/year from calendar label
        calendar_label = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["calendar_label"])))
        month_year_text = calendar_label.text  # e.g., "December 2025"
        print(f"  → Calendar shows: {month_year_text}")
        
        # Find available day buttons (typically have specific classes for available dates)
        # Look for clickable day cells
        available_days = driver.find_elements(By.CSS_SELECTOR, ".rbc-date-cell:not(.rbc-off-range) button")
        
        if not available_days:
            # Try alternative selector for available slots
            available_days = driver.find_elements(By.CSS_SELECTOR, ".rbc-day-slot .rbc-event")
        
        if available_days:
            # Get the first (earliest) available day
            first_day = available_days[0]
            day_num = first_day.text.strip()
            
            # Parse month/year
            date_obj = datetime.strptime(month_year_text, "%B %Y")
            
            # Format as MM/DD/YYYY
            formatted_date = f"{date_obj.month:02d}/{int(day_num):02d}/{date_obj.year}"
            print(f"  → Earliest available: {formatted_date}")
            return formatted_date
        else:
            print("  ⚠ No available dates found on current calendar view")
            return None
            
    except Exception as e:
        print(f"❌ Calendar parsing failed: {e}")
        return None


def compare_and_update_date(found_date: str, zip_code: str, params: dict) -> bool:
    """Compare found date with stored earliest and update if better."""
    print("🔄 Comparing dates...")
    
    try:
        found_dt = datetime.strptime(found_date, "%m/%d/%Y")
        
        if params["earliest_date"]:
            current_earliest = datetime.strptime(params["earliest_date"], "%m/%d/%Y")
        else:
            current_earliest = datetime.max
        
        if found_dt < current_earliest:
            print(f"  🎉 NEW EARLIER DATE FOUND! {found_date} < {params['earliest_date']}")
            update_parameters(new_date=found_date, new_zip=zip_code)
            return True
        else:
            print(f"  → Current date ({params['earliest_date']}) is still earliest")
            return False
            
    except Exception as e:
        print(f"❌ Date comparison failed: {e}")
        return False


# ============================================================================
# EPIC-6: LOOP & NOTIFICATION
# ============================================================================

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


def send_ntfy_notification(zip_code: str, date: str) -> None:
    """Send notification via NTFY.sh."""
    print("📢 Sending NTFY notification...")
    
    message = f"🎉 A new DMV availability has been found!\n\nZip Code: {zip_code}\nDate: {date}"
    
    try:
        response = requests.post(
            NTFY_URL,
            data=message.encode("utf-8"),
            headers={
                "Title": "DMV Appointment Alert!",
                "Priority": "high",
                "Tags": "calendar,car"
            }
        )
        
        if response.status_code == 200:
            print("✅ Notification sent successfully!")
        else:
            print(f"⚠ Notification failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("=" * 60)
    print("🚗 DMV Appointment Finder - Starting...")
    print("=" * 60)
    
    # Read parameters
    params = read_parameters()
    
    # Validate required parameters
    if not params["permit_number"]:
        print("❌ STOP: Permit Number is missing in parameters.md!")
        return
    if not params["dob"]:
        print("❌ STOP: Date of Birth is missing in parameters.md!")
        return
    if not params["zip_codes"]:
        print("❌ STOP: No Zip Codes found in parameters.md!")
        return
    
    print(f"📋 Parameters loaded:")
    print(f"   Permit: {params['permit_number']}")
    print(f"   DOB: {params['dob']}")
    print(f"   Zip Codes: {params['zip_codes']}")
    print(f"   Already Checked: {params['zip_codes_checked']}")
    print(f"   Current Earliest: {params['earliest_date']} ({params['earliest_zip']})")
    
    # Get unchecked zip codes
    unchecked_zips = get_unchecked_zip_codes(params)
    if not unchecked_zips:
        print("ℹ All zip codes have been checked. Resetting checked list...")
        # Reset for new round
        update_parameters(zip_checked="")
        unchecked_zips = params["zip_codes"]
    
    print(f"\n🎯 Will check {len(unchecked_zips)} zip codes: {unchecked_zips}")
    
    # Create browser
    driver = create_driver()
    better_date_found = False
    best_date = None
    best_zip = None
    
    try:
        # Epic-2: Login
        if not perform_login(driver, params):
            print("❌ ALERT: Login failed! Stopping.")
            return
        
        # Epic-3: Verify office page
        if not verify_office_page(driver):
            print("❌ ALERT: Office verification failed! Stopping.")
            return
        
        # Process each zip code
        for i, zip_code in enumerate(unchecked_zips):
            print(f"\n{'='*60}")
            print(f"📍 Processing zip code {i+1}/{len(unchecked_zips)}: {zip_code}")
            print("=" * 60)
            
            # Epic-3: Search for office
            if not search_office(driver, zip_code):
                continue
            
            # Epic-4: Select first office
            if not select_first_office(driver):
                continue
            
            # Epic-5: Read and compare dates
            found_date = parse_calendar_date(driver)
            if found_date:
                # Reload params to get latest earliest date
                current_params = read_parameters()
                if compare_and_update_date(found_date, zip_code, current_params):
                    better_date_found = True
                    best_date = found_date
                    best_zip = zip_code
            
            # Epic-6: Go back for next zip code (unless last one)
            if i < len(unchecked_zips) - 1:
                if not click_back_reset(driver):
                    print("⚠ Could not go back, attempting to continue...")
                    driver.get(DMV_URL)
                    random_delay(3, 5)
                    perform_login(driver, params)
                    verify_office_page(driver)
        
        # Epic-6: Send notification if better date found
        if better_date_found and best_date and best_zip:
            send_ntfy_notification(best_zip, best_date)
        
        print("\n" + "=" * 60)
        print("🏁 DMV Appointment Finder - Complete!")
        print("=" * 60)
        
        # Final summary
        final_params = read_parameters()
        print(f"\n📊 Final Results:")
        print(f"   Earliest Date: {final_params['earliest_date']}")
        print(f"   Earliest Zip: {final_params['earliest_zip']}")
        print(f"   Checked Zips: {final_params['zip_codes_checked']}")
        
    finally:
        random_delay(2, 3)
        driver.quit()
        print("\n👋 Browser closed. Goodbye!")


if __name__ == "__main__":
    main()
