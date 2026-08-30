import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

PRICING = {
    "1_month": 50000,
    "3_months": 130000,
    "lifetime": 300000
}