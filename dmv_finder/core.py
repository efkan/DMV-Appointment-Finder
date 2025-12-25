import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from dmv_finder.config import HEADLESS_MODE

def create_driver() -> webdriver.Chrome:
    """Create a simple Chrome WebDriver instance."""
    options = Options()
    
    if HEADLESS_MODE:
        options.add_argument("--headless=new") # Modern headless mode
        options.add_argument("--window-size=1920,1080")
        
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def random_delay(min_sec: float = 8.0, max_sec: float = 15.0) -> None:
    """Sleep for a random duration to mimic human behavior and avoid reCAPTCHA."""
    delay = random.uniform(min_sec, max_sec)
    print(f"  ⏳ Waiting {delay:.1f}s...")
    time.sleep(delay)

def human_type(element, text: str) -> None:
    """Type text character by character with random delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def check_for_captcha(driver) -> bool:
    """
    Check if a Google reCAPTCHA is actively requiring user interaction.
    Returns True if ACTIVE CAPTCHA challenge detected, False otherwise.
    
    Note: The CAPTCHA widget may always be present on the page, but we only
    care if it's actively blocking the user (showing a challenge).
    """
    # Indicators of an ACTIVE captcha challenge (not just widget presence)
    active_captcha_indicators = [
        "recaptcha-checkbox-checked",  # Already solved
        "rc-imageselect",              # Image challenge visible
        "rc-doscaptcha-body",          # "Try again later" message
        "recaptcha-verify-button",     # Verify button visible
    ]
    
    try:
        page_source = driver.page_source.lower()
        
        # Check if checkbox is already checked (solved) - this is fine
        if "recaptcha-checkbox-checked" in page_source:
            return False  # CAPTCHA is solved, no issue
        
        # Check for active challenge indicators
        for indicator in active_captcha_indicators[1:]:  # Skip the "checked" one
            if indicator.lower() in page_source:
                print(f"🛑 Active CAPTCHA challenge detected: {indicator}")
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠ CAPTCHA check error: {e}")
        return False

def handle_captcha_and_retry(driver, current_url: str, wait_minutes: int = 3) -> bool:
    """
    If CAPTCHA is detected, wait for specified minutes, reload page, and return True.
    Returns False if no CAPTCHA detected.
    """
    if not check_for_captcha(driver):
        return False  # No active CAPTCHA, proceed normally
    
    print(f"⏳ Waiting {wait_minutes} minutes before retrying...")
    time.sleep(wait_minutes * 60)
    
    print("🔄 Reloading page...")
    driver.get(current_url)
    random_delay(5, 10)  # Wait for page to load
    
    # Check again after reload
    if check_for_captcha(driver):
        print("🛑 CAPTCHA still active after waiting. Manual intervention may be needed.")
        return True  # Still blocked
    
    print("✅ CAPTCHA cleared! Continuing...")
    return False  # CAPTCHA cleared
