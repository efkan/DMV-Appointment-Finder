import requests
from .config import NTFY_URL

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
