# Blofin Trading Bot

A Python trading bot for Blofin demo account implementing a band-based strategy with position scaling and Telegram notifications.

## Features

- Band-based trading strategy
- Position scaling
- Telegram notifications
- Web interface for monitoring
- Volume-based pair scanning
- Real-time market analysis

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables in a `.env` file:
```
BLOFIN_API_KEY=your_api_key
BLOFIN_SECRET_KEY=your_secret_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

4. Run the bot:
```bash
python main.py
```

## Project Structure

- `main.py`: Entry point of the application
- `bot_control.py`: Bot control logic
- `config.py`: Configuration settings
- `exchange.py`: Exchange API integration
- `notifications.py`: Telegram notification system
- `scanner.py`: Market pair scanner
- `server.py`: Web interface server
- `strategy.py`: Trading strategy implementation
- `trading_bot.py`: Core trading bot logic
- `utils.py`: Utility functions
- `web_interface.py`: Web interface implementation

## License

MIT License
