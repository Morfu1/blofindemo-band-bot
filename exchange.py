import ccxt
import pandas as pd
from typing import Dict, List
from config import Config

class BlofingExchange:
    def __init__(self):
        self.exchange = ccxt.blofin({
            'apiKey': Config.API_KEY,
            'secret': Config.API_SECRET,
            'enableRateLimit': True
        })
        self.exchange.set_sandbox_mode(True)  # Use demo account

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Fetch OHLCV data from exchange"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def create_order(self, symbol: str, order_type: str, side: str, amount: float, 
                    price: float = None, params: Dict = None) -> Dict:
        """Create order on exchange"""
        try:
            return self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
        except Exception as e:
            raise Exception(f"Order creation failed: {str(e)}")

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for symbol"""
        try:
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            raise Exception(f"Setting leverage failed: {str(e)}")

    def set_margin_mode(self, symbol: str, isolated: bool):
        """Set margin mode for symbol"""
        try:
            mode = 'ISOLATED' if isolated else 'CROSS'
            self.exchange.set_margin_mode(mode, symbol)
        except Exception as e:
            raise Exception(f"Setting margin mode failed: {str(e)}")

    def get_positions(self, symbol: str) -> List[Dict]:
        """Get current positions"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            return [pos for pos in positions if float(pos['contracts']) > 0]
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {str(e)}")
