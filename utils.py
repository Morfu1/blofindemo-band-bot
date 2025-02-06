import logging
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )

def calculate_position_size(account_size: float, leverage: int, 
                          risk_percentage: float) -> float:
    """Calculate position size based on account size and risk"""
    return account_size * leverage * risk_percentage

def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe format"""
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    return timeframe in valid_timeframes
