import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "")

MIN_DEPOSIT_USD = Decimal(os.getenv("MIN_DEPOSIT_USD", "50"))
DEPOSIT_FEE_RATE = Decimal(os.getenv("DEPOSIT_FEE_RATE", "0.05"))
PROFIT_FEE_RATE = Decimal(os.getenv("PROFIT_FEE_RATE", "0.20"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///aurix.db")
