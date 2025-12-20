#!/usr/bin/env python3
"""
DMV Appointment Finder - California DMV Automation
Checks appointment slots and notifies via NTFY.sh when better dates are found.

Team:
- Product Manager: Atlas
- Senior Full-Stack Developer: Neo
- QA Engineer: Bugsy
"""

import sys
from datetime import datetime
from dmv_finder.config import DMV_URL
from dmv_finder.core import create_driver, random_delay
from dmv_finder.parameters import read_parameters, update_parameters, get_parameters
from dmv_finder.actions import (
    perform_login, 
    verify_office_page, 
    search_office, 
    select_first_office, 
    parse_calendar_date, 
    click_back_reset
)
from dmv_finder.notify import send_ntfy_notification


def compare_date(found_date: str, params: dict) -> bool:
    """Compare found date with stored earliest."""
    try:
        found_dt = datetime.strptime(found_date, "%m/%d/%Y")
        
        if params["earliest_date"]:
            current_earliest = datetime.strptime(params["earliest_date"], "%m/%d/%Y")
        else:
            current_earliest = datetime.max
        
        return found_dt < current_earliest
    except Exception as e:
        print(f"❌ Date comparison failed: {e}")
        return False


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
        print("❌ STOP: No Zip Codes found in parameters.md (or all checked)!")
        
        # If all zips are checked, maybe user wants to reset? 
        # But per instructions we just stop if no zips.
        # User said "remove it after the zip code is written to Zip Codes Checked".
        # So eventually this list will be empty.
        # Check if we should notify user they are all done.
        print("ℹ No zip codes to check based on parameters.md.")
        return
    
    print(f"📋 Parameters loaded:")
    print(f"   Permit: {params['permit_number']}")
    print(f"   DOB: {params['dob']}")
    print(f"   Zip Codes: {params['zip_codes']}")
    print(f"   Current Earliest: {params['earliest_date']} ({params['earliest_zip']})")
    
    # We iterate over a COPY of zip_codes because we might modify the file during iteration,
    # but `params` object is static here.
    # Note: `update_parameters` modifies the FILE, not the `params` dict in memory.
    zip_codes_to_process = list(params["zip_codes"])

    print(f"\n🎯 Will check {len(zip_codes_to_process)} zip codes: {zip_codes_to_process}")
    
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
        for i, zip_code in enumerate(zip_codes_to_process):
            print(f"\n{'='*60}")
            print(f"📍 Processing zip code {i+1}/{len(zip_codes_to_process)}: {zip_code}")
            print("=" * 60)
            
            # Epic-3: Search for office
            if not search_office(driver, zip_code):
                continue
            
            # Update parameters - mark zip as checked (and remove from list)
            # This is done immediately after successful search per requirements
            update_parameters(zip_checked=zip_code)
            print(f"  ✓ Zip code {zip_code} marked as checked & removed from list")
            
            # Epic-4: Select first office
            if not select_first_office(driver):
                continue
            
            # Epic-5: Read and compare dates
            found_date = parse_calendar_date(driver)
            if found_date:
                # Reload params to get latest earliest date (in case it changed or if logic needs it)
                # But we can just use the latest memory
                current_params = get_parameters()
                
                if compare_date(found_date, current_params):
                    print(f"  🎉 NEW EARLIER DATE FOUND! {found_date} < {current_params['earliest_date']}")
                    update_parameters(new_date=found_date, new_zip=zip_code)
                    
                    better_date_found = True
                    best_date = found_date
                    best_zip = zip_code
                else:
                    print(f"  → Current date ({current_params['earliest_date']}) is still earliest")
            
            # Epic-6: Go back for next zip code (unless last one)
            if i < len(zip_codes_to_process) - 1:
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
        print(f"   Remaining Zips: {final_params['zip_codes']}")
        
    finally:
        random_delay(2, 3)
        driver.quit()
        print("\n👋 Browser closed. Goodbye!")


if __name__ == "__main__":
    main()
