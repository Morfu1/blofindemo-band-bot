import logging
import asyncio
from telegram.ext import Application
from telegram.constants import ParseMode
from config import Config

class TelegramNotifier:
    def __init__(self):
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    def notify(self, message: str):
        """Send message to Telegram"""
        try:
            # Create event loop if it doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async send_message in the event loop
            loop.run_until_complete(self._send_message(message))
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {str(e)}")

    async def _send_message(self, message: str):
        """Async method to send message"""
        async with self.application:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )

    def format_trade_message(self, action: str, symbol: str, entry: float, 
                           tp: float, sl: float, size: float) -> str:
        """Format trade notification message"""
        return (
            f"🤖 <b>New Trade Alert</b>\n\n"
            f"Action: {action.upper()}\n"
            f"Symbol: {symbol}\n"
            f"Entry: {entry:.2f}\n"
            f"TP: {tp:.2f}\n"
            f"SL: {sl:.2f}\n"
            f"Size: {size:.2f} USD"
        )

    def format_scale_message(self, symbol: str, added_size: float, 
                           new_avg_entry: float, new_tp: float) -> str:
        """Format scale notification message"""
        return (
            f"🔄 <b>Position Scaled</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Added Size: {added_size:.2f} USD\n"
            f"New Avg Entry: {new_avg_entry:.2f}\n"
            f"New TP: {new_tp:.2f}"
        )