# Indian Standard Time timezone object — used throughout the app for timestamps
from datetime import timedelta, timezone

# Create IST timezone: UTC + 5 hours 30 minutes (India's timezone)
IST = timezone(timedelta(hours=5, minutes=30))
