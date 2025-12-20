import re

content = """
- Zip Codes: 
- Zip Codes Checked: 94568
"""

# Fixed Logic: Use [ \t]* instead of \s* to avoid crossing lines
match = re.search(r"Zip Codes:[ \t]*(?!Checked)(.+)", content)
if match:
    print(f"Match Found (Bad): '{match.group(1)}'")
else:
    print("No Match (Good!)")

content_valid = """
- Zip Codes: 12345
- Zip Codes Checked: 
"""
match_val = re.search(r"Zip Codes:[ \t]*(?!Checked)(.+)", content_valid)
if match_val:
    print(f"Valid Match: '{match_val.group(1).strip()}'")
else:
    print("Valid Logic Broken!")
