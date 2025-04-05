import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
PROOFS_CHANNEL_ID = int(os.getenv("PROOFS_CHANNEL_ID"))
STOREBOT_NAME = os.getenv("STOREBOT_NAME", "StoreBot")