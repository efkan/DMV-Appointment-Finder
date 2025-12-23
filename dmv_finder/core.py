import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
    Check if a Google reCAPTCHA is present on the page.
    Returns True if CAPTCHA detected, False otherwise.
    """
    captcha_indicators = [
        "g-recaptcha",
        "recaptcha-checkbox",
        "rc-anchor-container",
        "recaptcha-token",
    ]
    
    page_source = driver.page_source.lower()
    
    for indicator in captcha_indicators:
        if indicator.lower() in page_source:
            print("🛑 CAPTCHA DETECTED! Stopping execution.")
            return True
    
    return False
