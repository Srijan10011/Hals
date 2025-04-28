# config.py

# Telegram Bot settings
BOT_TOKEN          = "5938980093:AAHZmoqlEqujrKogYN6bm6J_DavjtEhml4s"
ADMIN_IDS          = [1155949927]             # Your Telegram user ID(s)
SESSION_FOLDER     = "sessions"               # Where your .session files live
RESERVATION_TIMEOUT = 300                     # Seconds before reserved number auto-frees

# Telegram API credentials for Telethon
API_ID   = 28863669
API_HASH = "72b4ff10bcce5ba17dba09f8aa526a44"

# The Telegram system bot that sends login codes
TG_BOT_ID = 777000

# How long to wait (in seconds) for an OTP before giving up
OTP_FETCH_TIMEOUT = 120

# Where to store last-seen OTP message IDs per session
STATE_FILE = "otp_state.json"
