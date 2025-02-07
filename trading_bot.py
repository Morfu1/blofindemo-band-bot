import logging
import time
from datetime import datetime
from config import Config
from exchange import BlofingExchange
from scanner import CoinScanner
from strategy import TradingStrategy
from notifications import TelegramNotifier
from bot_control import bot_controller

logger = logging.getLogger(__name__)

def get_next_candle_time(timeframe='5m'):
    """Calculate when the next candle will close"""
    current_time = datetime.now()
    minutes = int(timeframe[:-1])  # Extract minutes from timeframe
    remaining_seconds = (minutes - (current_time.minute % minutes)) * 60 - current_time.second
    return remaining_seconds + 2  # Add 2 seconds buffer

def run_trading_bot():
    """Run the trading bot with improved resilience for long-running sessions"""
    try:
        # Initialize components
        exchange = BlofingExchange()
        strategy = TradingStrategy(Config.SMA_PERIOD, Config.EMA_PERIOD)
        notifier = TelegramNotifier()
        scanner = CoinScanner(exchange, Config)

        logger.info(f"Bot started with max positions: {Config.MAX_POSITIONS}")
        logger.info(f"Position size: {Config.POSITION_SIZE} USDT, Leverage: {Config.LEVERAGE}x")
        logger.info(f"Total position value: {Config.POSITION_SIZE * Config.LEVERAGE} USDT")
        notifier.notify("🚀 Trading bot started!")

        # Initial scan
        logger.info("\n=== Initial Coin Scan ===")
        monitored_coins = scanner.get_top_volume_coins()
        logger.info(f"Initially monitoring {len(monitored_coins)} coins")

        last_status_update = datetime.now()
        reconnection_attempts = 0
        max_reconnection_attempts = 5

        while bot_controller.is_running():
            try:
                current_time = datetime.now()

                # Send status update every 6 hours
                if (current_time - last_status_update).total_seconds() > 21600:  # 6 hours
                    try:
                        positions = exchange.get_positions()
                        status_message = "📊 Bot Status Update:\n"
                        status_message += f"Active Positions: {len(positions)}/{Config.MAX_POSITIONS}\n"
                        status_message += f"Uptime: {(current_time - last_status_update).total_seconds() / 3600:.1f}h"
                        notifier.notify(status_message)
                        last_status_update = current_time
                        reconnection_attempts = 0  # Reset counter after successful operation
                    except Exception as e:
                        logger.error(f"Status update failed: {str(e)}")
                        if reconnection_attempts < max_reconnection_attempts:
                            reconnection_attempts += 1
                            time.sleep(60)  # Wait before retry
                            continue
                        else:
                            raise Exception("Max reconnection attempts reached")

                # Get current positions with retry logic
                try:
                    positions = exchange.get_positions()
                    logger.info(f"Current active positions: {len(positions)}")
                    reconnection_attempts = 0  # Reset counter after successful operation
                except Exception as e:
                    logger.error(f"Failed to fetch positions: {str(e)}")
                    if reconnection_attempts < max_reconnection_attempts:
                        reconnection_attempts += 1
                        time.sleep(60)
                        continue
                    else:
                        raise Exception("Max reconnection attempts reached")

                # Check for space for new positions
                if len(positions) < Config.MAX_POSITIONS:
                    opportunities = scanner.scan_for_opportunities(positions)

                    for opportunity in opportunities:
                        if not bot_controller.is_running():
                            break

                        symbol = opportunity['symbol']
                        signal = opportunity['signal']

                        # Calculate base position size (without leverage)
                        base_position_size = Config.POSITION_SIZE

                        # Set leverage for the symbol
                        try:
                            exchange.set_leverage(Config.LEVERAGE, symbol)
                        except Exception as e:
                            logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
                            continue

                        # Create order with proper SL/TP
                        side = 'buy' if signal['action'] == 'long' else 'sell'
                        try:
                            order = exchange.create_order(
                                symbol=symbol,
                                order_type='market',
                                side=side,
                                amount=base_position_size,
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
                                    base_position_size * Config.LEVERAGE
                                )
                            )
                            logger.info(f"Opened new {signal['action']} position on {symbol}")

                        except Exception as e:
                            logger.error(f"Failed to create order for {symbol}: {str(e)}")
                            continue

                # Wait for next candle
                sleep_time = get_next_candle_time(Config.TIMEFRAME)
                logger.info(f"Waiting {sleep_time} seconds for next {Config.TIMEFRAME} candle")

                # Check bot status more frequently
                for _ in range(sleep_time):
                    if not bot_controller.is_running():
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                if 'notifier' in locals():
                    notifier.notify(f"⚠️ Error: {str(e)}")
                time.sleep(60)

        # Notify bot stop
        if 'notifier' in locals():
            notifier.notify("🛑 Trading bot stopped!")
        logger.info("Trading bot stopped")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        if 'notifier' in locals():
            notifier.notify(f"❌ Fatal error: {str(e)}")