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
from dmv_finder.core import create_driver, random_delay, check_for_captcha, handle_captcha_and_retry
from dmv_finder.parameters import read_parameters, update_parameters, get_parameters, recycle_zip_codes
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
        
        print(f"  🔍 DEBUG: Comparing found {found_date} vs earliest {params['earliest_date']}")
        return found_dt < current_earliest
    except Exception as e:
        print(f"❌ Date comparison failed: {e}")
        return False


def run_cycle(driver):
    """Run one cycle of checking all zip codes."""
    print("=" * 60)
    print("🚗 DMV Appointment Finder - Starting Cycle...")
    print("=" * 60)
    
    # Read parameters
    params = read_parameters()
    
    # Validate required parameters
    if not params["permit_number"]:
        print("❌ STOP: Permit Number is missing in parameters.md!")
        return False
    if not params["dob"]:
        print("❌ STOP: Date of Birth is missing in parameters.md!")
        return False
    if not params["zip_codes"]:
        print("ℹ No zip codes to check. Recycling will happen at end of cycle.")
        # Don't return, let recycle happen
    
    print(f"📋 Parameters loaded:")
    print(f"   Permit: {params['permit_number']}")
    print(f"   DOB: {params['dob']}")
    print(f"   Zip Codes: {params['zip_codes']}")
    print(f"   Current Earliest: {params['earliest_date']} ({params['earliest_zip']})")
    
    zip_codes_to_process = list(params["zip_codes"])
    
    if not zip_codes_to_process:
        print("⚠ No zip codes to process in this cycle.")
        recycle_zip_codes()
        print("✅ Zip codes recycled for next cycle.")
        return True

    print(f"\n🎯 Will check {len(zip_codes_to_process)} zip codes: {zip_codes_to_process}")
    
    better_date_found = False
    best_date = None
    best_zip = None
    
    try:
        # Epic-2: Login
        if not perform_login(driver, params):
            print("❌ ALERT: Login failed! Will retry next cycle.")
            return False
        
        # Epic-3: Verify office page
        if not verify_office_page(driver):
            print("❌ ALERT: Office verification failed! Will retry next cycle.")
            return False
        
        # Check for CAPTCHA after login (wait and retry if needed)
        if handle_captcha_and_retry(driver, DMV_URL):
            print("❌ ALERT: CAPTCHA still blocking after retry! Will retry next cycle.")
            return False
        
        # Process each zip code
        for i, zip_code in enumerate(zip_codes_to_process):
            print(f"\n{'='*60}")
            print(f"📍 Processing zip code {i+1}/{len(zip_codes_to_process)}: {zip_code}")
            print("=" * 60)
            
            # Check for CAPTCHA before each zip code search (wait and retry if needed)
            if handle_captcha_and_retry(driver, driver.current_url):
                print("❌ ALERT: CAPTCHA still blocking! Skipping this iteration.")
                continue  # Try next zip code
            
            # Epic-3: Search for office
            if not search_office(driver, zip_code):
                continue
            
            # Update parameters - mark zip as checked (and remove from list)
            update_parameters(zip_checked=zip_code)
            print(f"  ✓ Zip code {zip_code} marked as checked & removed from list")
            
            # Epic-4: Select first office
            if not select_first_office(driver):
                continue
            
            # Epic-5: Read and compare dates
            found_date = parse_calendar_date(driver)
            if found_date:
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
            send_ntfy_notification(best_date, best_zip)
        
        print("\n" + "=" * 60)
        print("🏁 DMV Appointment Finder - Cycle Complete!")
        print("=" * 60)
        
        # Final summary
        final_params = read_parameters()
        print(f"\n📊 Cycle Results:")
        print(f"   Earliest Date: {final_params['earliest_date']}")
        print(f"   Earliest Zip: {final_params['earliest_zip']}")
        print(f"   Remaining Zips: {final_params['zip_codes']}")
        
        # Recycle checked zip codes
        print("\n♻️ Recycling checked zip codes...")
        recycle_zip_codes()
        print("✅ Zip codes recycled.")
        
        return True
        
    except Exception as e:
        print(f"❌ Cycle error: {e}")
        return False


def main():
    """Main execution flow - runs continuously."""
    print("🔄 Starting DMV Appointment Finder in CONTINUOUS MODE")
    print("   Press Ctrl+C to stop.\n")
    
    driver = create_driver()
    cycle_count = 0
    wait_minutes = 10
    
    try:
        while True:
            cycle_count += 1
            print(f"\n{'#'*60}")
            print(f"# CYCLE {cycle_count}")
            print(f"{'#'*60}\n")
            
            success = run_cycle(driver)
            
            if not success:
                print("⚠ Cycle had issues. Will retry after wait.")
            
            print(f"\n⏳ Waiting {wait_minutes} minutes before next cycle...")
            import time
            time.sleep(wait_minutes * 60)
            
            # Navigate back to start for next cycle
            print("🔄 Reloading for next cycle...")
            driver.get(DMV_URL)
            random_delay(3, 5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user (Ctrl+C)")
    finally:
        random_delay(2, 3)
        driver.quit()
        print("\n👋 Browser closed. Goodbye!")


if __name__ == "__main__":
    main()

