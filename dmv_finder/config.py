from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
PARAMETERS_FILE = BASE_DIR / "Management" / "parameters.md"

# URL
DMV_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type"

# NTFY
NTFY_TOPIC = "pinars_dmv_appointments"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# Selectors
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
    # Calendar navigation
    "next_month_btn": "#appointments-react-root > section > div.appointments__main > div.appointments__calendar-container > div.rbc-calendar > div.rbc-toolbar > span:nth-child(3) > button:nth-child(2)",
}
