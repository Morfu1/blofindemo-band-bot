import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_KEY = os.getenv('BLOFIN_API_KEY')
    API_SECRET = os.getenv('BLOFIN_API_SECRET')
    API_PASSWORD = os.getenv('BLOFIN_PASSWORD')

    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # Trading Parameters
    TIMEFRAME = os.getenv('TIMEFRAME', '5m')  # Changed default to 5m
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '100'))
    LEVERAGE = int(os.getenv('LEVERAGE', '3'))
    ISOLATED = os.getenv('ISOLATED', 'True').lower() == 'true'
    SYMBOL = os.getenv('SYMBOL', 'BTC-USDT')
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '3'))  # Maximum number of concurrent positions
    TOP_COINS_TO_SCAN = int(os.getenv('TOP_COINS_TO_SCAN', '10'))  # Number of top volume coins to scan

    # Strategy Parameters
    TP_PERCENTAGE = 0.02  # 2%
    SL_PERCENTAGE = 0.01  # 1%
    SCALE_MULTIPLIER = 1.1
    SMA_PERIOD = 21
    EMA_PERIOD = 34

    @classmethod
    def validate(cls):
        required_fields = ['API_KEY', 'API_SECRET', 'API_PASSWORD', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_fields = [field for field in required_fields if not getattr(cls, field)]

        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")