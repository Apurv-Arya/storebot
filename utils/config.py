import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

COINPAYMENTS_API_KEY = os.getenv("CP_API_KEY")
COINPAYMENTS_API_SECRET = os.getenv("CP_API_SECRET")
