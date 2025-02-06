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
        logger.info(f"Setting up trading parameters for {Config.SYMBOL}")
        exchange.set_leverage(Config.SYMBOL, Config.LEVERAGE)

        logger.info(f"Bot started with symbol {Config.SYMBOL} on timeframe {Config.TIMEFRAME}")
        notifier.notify("🚀 Trading bot started!")

        while True:
            try:
                # Fetch market data
                logger.info(f"Fetching OHLCV data for {Config.SYMBOL}")
                data = exchange.fetch_ohlcv(Config.SYMBOL, Config.TIMEFRAME)
                if data.empty:
                    logger.warning("No market data available")
                    time.sleep(60)
                    continue

                # Get current positions
                positions = exchange.get_positions(Config.SYMBOL)
                if positions:
                    logger.info(f"Current positions: {positions}")

                # Get trading signal
                signal = strategy.get_signal(data)
                logger.info(f"Current signal: {signal['action']}")
                logger.info(f"Band levels - Upper: {signal.get('upper_band', 'N/A')}, Lower: {signal.get('lower_band', 'N/A')}")
                logger.info(f"Current price: {data['close'].iloc[-1]}")

                if positions:
                    # Check for scaling opportunity
                    position = positions[0]
                    position_type = 'long' if position['side'] == 'buy' else 'short'
                    current_price = float(data['close'].iloc[-1])

                    if strategy.should_scale_position(data, position_type):
                        logger.info(f"Scaling {position_type} position")
                        scale_size = Config.POSITION_SIZE * Config.SCALE_MULTIPLIER

                        # Create scaling order with new TP
                        new_tp = strategy.calculate_new_tp(current_price, positions)

                        order = exchange.create_order(
                            symbol=Config.SYMBOL,
                            order_type='market',
                            side=position['side'],
                            amount=scale_size,
                            params={
                                'takeProfit': {
                                    'price': new_tp,
                                    'type': 'market'
                                }
                            }
                        )

                        # Notify about scaling
                        notifier.notify(
                            notifier.format_scale_message(
                                Config.SYMBOL,
                                scale_size,
                                order['price'],
                                new_tp
                            )
                        )
                        logger.info(f"Scaled {position_type} position with size {scale_size}")

                elif signal['action']:
                    # Create new position
                    side = 'buy' if signal['action'] == 'long' else 'sell'
                    logger.info(f"Opening new {signal['action']} position at {Config.TIMEFRAME} timeframe")

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
                    logger.info(f"Opened new {signal['action']} position with SL at {signal['sl_price']} and TP at {signal['tp_price']}")

                # Sleep before next iteration
                time.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                notifier.notify(f"⚠️ Error: {str(e)}")
                time.sleep(60)  # Wait before retrying

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        if 'notifier' in locals():
            notifier.notify(f"❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    main()