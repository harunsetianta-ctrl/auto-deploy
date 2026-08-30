import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
DATABASE_URL = os.environ.get("DATABASE_URL")

PRICING = {
    "1_month": 1000,
    "3_months": 130000,
    "lifetime": 300000
}

# --- AutoKuy Pay ---
AUTOKUY_BASE_URL = os.environ.get("AUTOKUY_BASE_URL", "https://payment.kuskuskuy.my.id")
AUTOKUY_API_KEY = os.environ.get("AUTOKUY_API_KEY")          # akp_live_xxx / akp_test_xxx
AUTOKUY_WEBHOOK_SECRET = os.environ.get("AUTOKUY_WEBHOOK_SECRET")

# Port for the local webhook server that receives AutoKuy Pay callbacks
WEBHOOK_PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = "/webhook/autokuy"
