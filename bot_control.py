import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class BotController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotController, cls).__new__(cls)
            cls._instance.bot_thread: Optional[threading.Thread] = None
            cls._instance.bot_running: bool = False
        return cls._instance

    def start_bot(self, bot_function) -> bool:
        """Start the trading bot"""
        with self._lock:
            if self.bot_running:
                logger.warning("Bot is already running")
                return False

            try:
                self.bot_running = True
                self.bot_thread = threading.Thread(target=bot_function)
                self.bot_thread.daemon = True
                self.bot_thread.start()
                logger.info("Trading bot started successfully")
                return True
            except Exception as e:
                self.bot_running = False
                logger.error(f"Failed to start bot: {str(e)}")
                return False

    def stop_bot(self) -> bool:
        """Stop the trading bot"""
        with self._lock:
            if not self.bot_running:
                logger.warning("Bot is not running")
                return False

            try:
                self.bot_running = False
                if self.bot_thread:
                    self.bot_thread.join(timeout=1.0)
                logger.info("Trading bot stopped successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to stop bot: {str(e)}")
                return False

    def is_running(self) -> bool:
        """Check if the bot is currently running"""
        with self._lock:
            return self.bot_running

# Global instance
bot_controller = BotController()