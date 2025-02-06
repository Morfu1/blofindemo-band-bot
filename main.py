import time
import logging
import threading
from config import Config
from utils import setup_logging, validate_timeframe
from server import start_server
from trading_bot import run_trading_bot

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Validate configuration
        Config.validate()
        if not validate_timeframe(Config.TIMEFRAME):
            raise ValueError(f"Invalid timeframe: {Config.TIMEFRAME}")

        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_server)
        web_thread.daemon = True
        web_thread.start()
        logger.info("Web interface started")

        # Wait for web server to be ready
        time.sleep(5)  # Give the web server time to start

        # Keep the main thread running
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")

if __name__ == "__main__":
    main()