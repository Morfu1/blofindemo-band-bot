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
    """Run the trading bot"""
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

        while bot_controller.is_running():
            try:
                # Get current positions
                positions = exchange.get_positions()
                logger.info(f"Current active positions: {len(positions)}")

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
