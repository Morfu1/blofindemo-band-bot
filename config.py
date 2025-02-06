import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_KEY = os.getenv('BLOFIN_API_KEY')
    API_SECRET = os.getenv('BLOFIN_API_SECRET')
    
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading Parameters
    TIMEFRAME = os.getenv('TIMEFRAME', '1h')
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '100'))
    LEVERAGE = int(os.getenv('LEVERAGE', '3'))
    ISOLATED = os.getenv('ISOLATED', 'True').lower() == 'true'
    SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
    
    # Strategy Parameters
    TP_PERCENTAGE = 0.02  # 2%
    SL_PERCENTAGE = 0.01  # 1%
    SCALE_MULTIPLIER = 1.1
    SMA_PERIOD = 21
    EMA_PERIOD = 34

    @classmethod
    def validate(cls):
        required_fields = ['API_KEY', 'API_SECRET', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_fields = [field for field in required_fields if not getattr(cls, field)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
