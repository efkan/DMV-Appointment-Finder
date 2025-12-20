import re
from typing import Dict, List, Optional
from .config import PARAMETERS_FILE

def read_parameters() -> Dict:
    """Read parameters from parameters.md file."""
    params = {
        "zip_codes": [],
        "zip_codes_checked": [],
        "permit_number": "",
        "dob": "",
        "earliest_date": "",
        "earliest_zip": "",
    }
    
    if not PARAMETERS_FILE.exists():
        return params

    content = PARAMETERS_FILE.read_text()
    
    # Parse zip codes: Match "Zip Codes:" but exclude "Zip Codes Checked:" line
    # (?!Checked) ensures we don't match the checked line
    zip_match = re.search(r"Zip Codes:\s*(?!Checked)(.+)", content)
    if zip_match:
        zips_str = zip_match.group(1).strip()
        if zips_str:
            params["zip_codes"] = [z.strip() for z in zips_str.split(",") if z.strip()]
    
    # Parse checked zip codes
    checked_match = re.search(r"Zip Codes Checked:\s*(.*)", content)
    if checked_match:
        checked_str = checked_match.group(1).strip()
        if checked_str:
            params["zip_codes_checked"] = [z.strip() for z in checked_str.split(",") if z.strip()]
    
    # Parse permit number
    permit_match = re.search(r"Permit Number:\s*(\S+)", content)
    if permit_match:
        params["permit_number"] = permit_match.group(1).strip()
    
    # Parse DOB
    dob_match = re.search(r"Date of Birth:\s*(\S+)", content)
    if dob_match:
        params["dob"] = dob_match.group(1).strip()
    
    # Parse earliest availability (allowing for spaces or other chars)
    earliest_zip_match = re.search(r"Found Earliest Availability Zip Code:\s*(.*)", content)
    if earliest_zip_match:
        params["earliest_zip"] = earliest_zip_match.group(1).strip()
    
    earliest_date_match = re.search(r"Found Earliest Availability Date:\s*(.*)", content)
    if earliest_date_match:
        params["earliest_date"] = earliest_date_match.group(1).strip()
    
    return params

def update_parameters(zip_checked: Optional[str] = None, new_date: Optional[str] = None, new_zip: Optional[str] = None) -> None:
    """
    Update parameters.md:
    1. If zip_checked provided: remove from "Zip Codes" and add to "Zip Codes Checked".
    2. If new_date/new_zip provided: update the earliest availability fields.
    """
    content = PARAMETERS_FILE.read_text()
    
    if zip_checked:
        # 1. Add to Zip Codes Checked
        checked_match = re.search(r"(Zip Codes Checked:)(.*)", content)
        if checked_match:
            existing = checked_match.group(2).strip()
            if existing:
                if zip_checked not in existing:
                     new_checked = f"{existing}, {zip_checked}"
                else:
                     new_checked = existing
            else:
                new_checked = zip_checked
            
            # Using .* to match rest of line regardless of bullet preference
            content = re.sub(
                r"Zip Codes Checked:.*",
                f"Zip Codes Checked: {new_checked}",
                content
            )
        
        # 2. Remove from Zip Codes
        # Match 'Zip Codes:' avoiding 'Checked'
        zips_match = re.search(r"(Zip Codes:\s*(?!Checked))(.+)", content)
        if zips_match:
            prefix = zips_match.group(1) # e.g. "Zip Codes: " or "- Zip Codes: " if matched safely?
            # Re-read careful regex: group 1 involves the lookahead, might be tricky.
            # Simpler to parse the values.
            current_zips_str = zips_match.group(2).strip()
            if current_zips_str:
                zips_list = [z.strip() for z in current_zips_str.split(",") if z.strip()]
                if zip_checked in zips_list:
                    zips_list.remove(zip_checked)
                    new_zips_str = ", ".join(zips_list)
                    
                    # Replace the line. We use the same lookahead logic
                    content = re.sub(
                        r"Zip Codes:\s*(?!Checked).*",
                        f"Zip Codes: {new_zips_str}",
                        content
                    )

    if new_date:
        content = re.sub(
            r"Found Earliest Availability Date:.*",
            f"Found Earliest Availability Date: {new_date}",
            content
        )
    
    if new_zip:
        content = re.sub(
            r"Found Earliest Availability Zip Code:.*",
            f"Found Earliest Availability Zip Code: {new_zip}",
            content
        )
    
    PARAMETERS_FILE.write_text(content)

def recycle_zip_codes() -> None:
    """
    Move all 'Zip Codes Checked' back to 'Zip Codes' and clear Checked list.
    """
    if not PARAMETERS_FILE.exists():
        return
        
    content = PARAMETERS_FILE.read_text()
    
    # Extract checked zip codes
    checked_match = re.search(r"Zip Codes Checked:\s*(.+)", content)
    if not checked_match or not checked_match.group(1).strip():
        # Nothing to recycle
        return
        
    checked_zips_str = checked_match.group(1).strip()
    
    # 1. Clear Zip Codes Checked
    content = re.sub(
        r"Zip Codes Checked:.*",
        "Zip Codes Checked: ",
        content
    )
    
    # 2. Append to Zip Codes
    # Find existing Zip Codes line
    zips_match = re.search(r"(Zip Codes:\s*(?!Checked))(.+)", content)
    
    if zips_match:
        current_zips = zips_match.group(2).strip()
        if current_zips:
            new_zips = f"{current_zips}, {checked_zips_str}"
        else:
            new_zips = checked_zips_str
            
        content = re.sub(
            r"Zip Codes:\s*(?!Checked).*",
            f"Zip Codes: {new_zips}",
            content
        )
    else:
        # If Zip Codes line is empty or missing (edge case), just set it
        # This regex replacement handles the line if it exists but is empty
        content = re.sub(
            r"Zip Codes:\s*(?!Checked).*",
            f"Zip Codes: {checked_zips_str}",
            content
        )

    PARAMETERS_FILE.write_text(content)

def get_parameters() -> Dict:
    """Simple alias to be consistent."""
    return read_parameters()
