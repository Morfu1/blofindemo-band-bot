import ccxt
import pandas as pd
from typing import Dict, List
from config import Config
import logging

class BlofingExchange:
    def __init__(self):
        self.exchange = ccxt.blofin({
            'apiKey': Config.API_KEY,
            'secret': Config.API_SECRET,
            'password': Config.API_PASSWORD,
            'enableRateLimit': True
        })
        self.exchange.set_sandbox_mode(True)  # Use demo account
        self.logger = logging.getLogger(__name__)

    def create_order(self, symbol: str, order_type: str, side: str, amount: float, 
                    price: float = None, params: Dict = None) -> Dict:
        """Create order on exchange with enhanced validation"""
        try:
            # Validate input parameters
            if order_type not in ['market', 'limit']:
                raise ValueError(f"Invalid order type: {order_type}")
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if order_type == 'limit' and (price is None or price <= 0):
                raise ValueError("Valid price required for limit orders")

            # Get current market price for proper SL/TP calculation
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            # Format SL/TP parameters for Blofin API
            default_params = {
                'marginMode': 'isolated' if Config.ISOLATED else 'cross',
                'tdMode': 'isolated' if Config.ISOLATED else 'cross',
                'lever': str(Config.LEVERAGE)
            }

            if params and 'stopLoss' in params:
                sl_price = params['stopLoss']['price']
                default_params.update({
                    'slTriggerPx': str(sl_price),  # Trigger price
                    'slOrdPx': str(sl_price),      # Order price
                })
                self.logger.info(f"Setting SL price to: {sl_price}")

            if params and 'takeProfit' in params:
                tp_price = params['takeProfit']['price']
                default_params.update({
                    'tpTriggerPx': str(tp_price),  # Trigger price
                    'tpOrdPx': str(tp_price),      # Order price
                })
                self.logger.info(f"Setting TP price to: {tp_price}")

            # Log the final parameters
            merged_params = {**default_params, **(params or {})}
            self.logger.info(f"Creating order with params: {merged_params}")

            # Create the order
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=merged_params
            )

            self.logger.info(f"Order created successfully: {order}")
            return order

        except Exception as e:
            self.logger.error(f"Order creation failed: {str(e)}")
            raise

    def fetch_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Fetch OHLCV data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            raise Exception(f"Failed to fetch OHLCV data: {str(e)}")

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for symbol"""
        try:
            if leverage <= 0:
                raise ValueError("Leverage must be positive")
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            raise Exception(f"Setting leverage failed: {str(e)}")

    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get current positions with enhanced error handling"""
        try:
            if symbol:
                positions = self.exchange.fetch_positions([symbol])
            else:
                positions = self.exchange.fetch_positions()
            return [pos for pos in positions if float(pos['contracts']) > 0]
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {str(e)}")