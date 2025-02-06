import time
import logging
import threading
from datetime import datetime
from config import Config
from strategy import TradingStrategy
from exchange import BlofingExchange
from notifications import TelegramNotifier
from scanner import CoinScanner
from utils import setup_logging, validate_timeframe
from server import start_server
from bot_control import bot_controller

def is_candle_closed(data):
    """Check if the latest candle is newly closed"""
    if data.empty:
        return False
    latest_candle_time = data.iloc[-1]['timestamp']
    current_time = datetime.now()
    time_diff = (current_time - latest_candle_time).total_seconds()
    return time_diff < 60  # Consider candle closed if it's less than 1 minute old

def get_next_candle_time(timeframe='5m'):
    """Calculate when the next candle will close"""
    current_time = datetime.now()
    minutes = int(timeframe[:-1])  # Extract minutes from timeframe
    remaining_seconds = (minutes - (current_time.minute % minutes)) * 60 - current_time.second
    return remaining_seconds + 2  # Add 2 seconds buffer

def run_trading_bot():
    logger = logging.getLogger(__name__)

    try:
        # Initialize components
        exchange = BlofingExchange()
        strategy = TradingStrategy(Config.SMA_PERIOD, Config.EMA_PERIOD)
        notifier = TelegramNotifier()
        scanner = CoinScanner(exchange, Config)

        logger.info(f"Bot started with max positions: {Config.MAX_POSITIONS}")
        notifier.notify("🚀 Trading bot started!")

        # Initial scan to show monitored coins
        logger.info("\n=== Initial Coin Scan ===")
        monitored_coins = scanner.get_top_volume_coins()
        logger.info(f"Initially monitoring {len(monitored_coins)} coins")

        while bot_controller.is_running():  # Check bot_running flag
            try:
                # Get current positions
                positions = exchange.get_positions()
                logger.info(f"Current active positions: {len(positions)}")

                # Wait for next candle close before scanning
                sleep_time = get_next_candle_time(Config.TIMEFRAME)
                logger.info(f"Waiting {sleep_time} seconds for next {Config.TIMEFRAME} candle close")

                # Use smaller sleep intervals to check bot_running flag more frequently
                for _ in range(sleep_time):
                    if not bot_controller.is_running():
                        break
                    time.sleep(1)

                if not bot_controller.is_running():
                    break

                # Check for new opportunities if we have room for more positions
                if len(positions) < Config.MAX_POSITIONS:
                    opportunities = scanner.scan_for_opportunities(positions)

                    for opportunity in opportunities:
                        if not bot_controller.is_running():
                            break

                        symbol = opportunity['symbol']
                        signal = opportunity['signal']

                        # Create new position
                        side = 'buy' if signal['action'] == 'long' else 'sell'
                        logger.info(f"Opening new {signal['action']} position for {symbol}")

                        try:
                            order = exchange.create_order(
                                symbol=symbol,
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
                                    symbol,
                                    signal['entry_price'],
                                    signal['tp_price'],
                                    signal['sl_price'],
                                    Config.POSITION_SIZE
                                )
                            )
                            logger.info(f"Opened new {signal['action']} position on {symbol}")
                        except Exception as e:
                            logger.error(f"Failed to create order for {symbol}: {str(e)}")
                            continue

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                if 'notifier' in locals():
                    notifier.notify(f"⚠️ Error: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying after error

        # Notify that the bot has stopped
        if 'notifier' in locals():
            notifier.notify("🛑 Trading bot stopped!")
        logger.info("Trading bot stopped")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        if 'notifier' in locals():
            notifier.notify(f"❌ Fatal error: {str(e)}")

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Validate configuration
        Config.validate()
        if not validate_timeframe(Config.TIMEFRAME):
            raise ValueError(f"Invalid timeframe: {Config.TIMEFRAME}")

        # Start web interface in a separate thread
        web_thread = threading.Thread(target=start_server)
        web_thread.daemon = True
        web_thread.start()
        logger.info("Web interface started on port 5001")

        # Start trading bot in main thread
        run_trading_bot()

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")

if __name__ == "__main__":
    main()