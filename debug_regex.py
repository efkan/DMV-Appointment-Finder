import re

content_ok = """
- Zip Codes: 94568, 95304
- Zip Codes Checked: 
"""

content_bad = """
- Zip Codes: 
- Zip Codes Checked: 94568
"""

# Current Logic
match = re.search(r"Zip Codes:\s*(?!Checked)(.+)", content_bad)
if match:
    print(f"Current Logic Match: '{match.group(1)}'")
else:
    print("Current Logic: No match")

# Proposed Logic (Strict)
match_strict = re.search(r"^\s*-\s*Zip Codes:\s*(.+)", content_bad, re.MULTILINE)
if match_strict:
    print(f"Strict Logic Match: '{match_strict.group(1)}'")
else:
    print("Strict Logic: No match")
