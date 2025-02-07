import ccxt
import pandas as pd
import time
from typing import Dict, List
from config import Config
import logging

class BlofingExchange:
    def __init__(self):
        self.exchange = self._initialize_exchange()
        self.logger = logging.getLogger(__name__)
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5  # seconds

    def _initialize_exchange(self):
        """Initialize exchange with retries"""
        exchange = ccxt.blofin({
            'apiKey': Config.API_KEY,
            'secret': Config.API_SECRET,
            'password': Config.API_PASSWORD,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 seconds timeout
        })
        exchange.set_sandbox_mode(True)  # Use demo account
        return exchange

    def _handle_request(self, operation, *args, **kwargs):
        """Handle exchange requests with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except ccxt.NetworkError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                self.logger.warning(f"Network error, retrying... ({attempt + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
            except ccxt.ExchangeError as e:
                if 'unauthorized' in str(e).lower():
                    self.exchange = self._initialize_exchange()
                if attempt == self.MAX_RETRIES - 1:
                    raise
                self.logger.warning(f"Exchange error, retrying... ({attempt + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)

    def create_order(self, symbol: str, order_type: str, side: str, amount: float, 
                    price: float = None, params: Dict = None) -> Dict:
        """Create order with improved error handling and correct position sizing"""
        try:
            if order_type not in ['market', 'limit']:
                raise ValueError(f"Invalid order type: {order_type}")
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if order_type == 'limit' and (price is None or price <= 0):
                raise ValueError("Valid price required for limit orders")

            # Get current market price for calculating correct position size
            ticker = self._handle_request(self.exchange.fetch_ticker, symbol)
            current_price = ticker['last']

            # Calculate the correct position size based on USD amount and leverage
            # amount parameter is in USD, we need to convert it to the asset quantity
            position_size_usd = amount * Config.LEVERAGE
            quantity = position_size_usd / current_price

            # Prepare order parameters
            default_params = {
                'marginMode': 'isolated' if Config.ISOLATED else 'cross',
                'tdMode': 'isolated' if Config.ISOLATED else 'cross',
                'lever': str(Config.LEVERAGE)
            }

            if params:
                if 'stopLoss' in params:
                    sl_price = params['stopLoss']['price']
                    default_params.update({
                        'slTriggerPx': str(sl_price),
                        'slOrdPx': str(sl_price),
                        'slTpMode': 'Full'
                    })
                    self.logger.info(f"Setting SL price to: {sl_price}")

                if 'takeProfit' in params:
                    tp_price = params['takeProfit']['price']
                    default_params.update({
                        'tpTriggerPx': str(tp_price),
                        'tpOrdPx': str(tp_price),
                        'slTpMode': 'Full'
                    })
                    self.logger.info(f"Setting TP price to: {tp_price}")

            merged_params = {**default_params, **(params or {})}
            self.logger.info(f"Creating order with params: {merged_params}")

            # Create the order with retry logic
            order = self._handle_request(
                self.exchange.create_order,
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity,  # Use the calculated quantity
                price=price,
                params=merged_params
            )

            self.logger.info(f"Order created successfully: {order}")
            return order

        except Exception as e:
            self.logger.error(f"Order creation failed: {str(e)}")
            raise

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Fetch OHLCV data with retry logic"""
        try:
            ohlcv = self._handle_request(self.exchange.fetch_ohlcv, symbol, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            raise Exception(f"Failed to fetch OHLCV data: {str(e)}")

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage with retry logic"""
        try:
            if leverage <= 0:
                raise ValueError("Leverage must be positive")
            self._handle_request(self.exchange.set_leverage, leverage, symbol)
        except Exception as e:
            raise Exception(f"Setting leverage failed: {str(e)}")

    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get current positions with retry logic"""
        try:
            if symbol:
                positions = self._handle_request(self.exchange.fetch_positions, [symbol])
            else:
                positions = self._handle_request(self.exchange.fetch_positions)
            return [pos for pos in positions if float(pos['contracts']) > 0]
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {str(e)}")