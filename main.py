import time
import logging
from config import Config
from strategy import TradingStrategy
from exchange import BlofingExchange
from notifications import TelegramNotifier
from utils import setup_logging, validate_timeframe

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        Config.validate()
        if not validate_timeframe(Config.TIMEFRAME):
            raise ValueError(f"Invalid timeframe: {Config.TIMEFRAME}")

        # Initialize components
        exchange = BlofingExchange()
        strategy = TradingStrategy(Config.SMA_PERIOD, Config.EMA_PERIOD)
        notifier = TelegramNotifier()

        # Set up trading parameters
        exchange.set_leverage(Config.SYMBOL, Config.LEVERAGE)
        exchange.set_margin_mode(Config.SYMBOL, Config.ISOLATED)

        logger.info(f"Bot started with symbol {Config.SYMBOL}")
        notifier.notify("🚀 Trading bot started!")

        while True:
            try:
                # Fetch market data
                data = exchange.fetch_ohlcv(Config.SYMBOL, Config.TIMEFRAME)
                
                # Get current positions
                positions = exchange.get_positions(Config.SYMBOL)
                
                # Get trading signal
                signal = strategy.get_signal(data)
                
                if positions:
                    # Check for scaling opportunity
                    position = positions[0]
                    position_type = 'long' if position['side'] == 'buy' else 'short'
                    
                    if strategy.should_scale_position(data, position_type):
                        scale_size = Config.POSITION_SIZE * Config.SCALE_MULTIPLIER
                        
                        # Create scaling order
                        order = exchange.create_order(
                            symbol=Config.SYMBOL,
                            order_type='market',
                            side=position['side'],
                            amount=scale_size
                        )
                        
                        # Calculate new TP
                        new_tp = strategy.calculate_new_tp(positions + [order])
                        
                        # Notify about scaling
                        notifier.notify(
                            notifier.format_scale_message(
                                Config.SYMBOL,
                                scale_size,
                                order['price'],
                                new_tp
                            )
                        )
                
                elif signal['action']:
                    # Create new position
                    side = 'buy' if signal['action'] == 'long' else 'sell'
                    
                    order = exchange.create_order(
                        symbol=Config.SYMBOL,
                        order_type='market',
                        side=side,
                        amount=Config.POSITION_SIZE,
                        params={
                            'stopLoss': {
                                'price': signal['sl_price'],
                                'type': 'market'
                            },
                            'takeProfit': {
                                'price': signal['tp_price'],
                                'type': 'market'
                            }
                        }
                    )
                    
                    # Notify about new position
                    notifier.notify(
                        notifier.format_trade_message(
                            signal['action'],
                            Config.SYMBOL,
                            signal['entry_price'],
                            signal['tp_price'],
                            signal['sl_price'],
                            Config.POSITION_SIZE
                        )
                    )
                
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                notifier.notify(f"⚠️ Error: {str(e)}")
                time.sleep(60)  # Wait before retrying

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        notifier.notify(f"❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
