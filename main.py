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

        # Start web server in a separate thread with proper error handling
        web_thread = threading.Thread(target=start_server)
        web_thread.daemon = True
        web_thread.start()
        logger.info("Web server thread started")

        # Wait for web server to be ready
        server_wait_time = 0
        max_wait_time = 30  # Maximum time to wait for server (seconds)
        while server_wait_time < max_wait_time:
            try:
                import requests
                response = requests.get('http://0.0.0.0:8080/')
                if response.status_code == 200:
                    logger.info("Web server is up and running")
                    break
            except:
                server_wait_time += 1
                time.sleep(1)
                continue

        if server_wait_time >= max_wait_time:
            logger.error("Web server failed to start within the timeout period")
            raise Exception("Web server startup timeout")

        # Keep the main thread running
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")

if __name__ == "__main__":
    main()