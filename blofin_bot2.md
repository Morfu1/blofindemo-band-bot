# Implementing a Trading Strategy Using Blofin Demo Account and Python

## Introduction

This documentation guides users through the process of using a Blofin Demo account to implement a trading strategy in a Python-based bot. The strategy involves using SMA 21 and EMA 34 bands to determine entry points. Positions are opened on the first candle after the price closes outside the bands, with configurable take-profit and stop-loss levels based on the band's position.

## Prerequisites

Before implementing the strategy, ensure the following steps are completed:

1. **Set Up a Blofin Demo Account**:
   - Register for a Blofin account.
   - Enable Two-Factor Authentication (2FA) for enhanced security.
   - Familiarize yourself with the Blofin platform.

2. **Install Necessary Python Libraries**:
   - Install the [Blofin Python SDK](https://github.com/nomeida/blofin-python) for interacting with the API.
   - Install `pandas` for data manipulation and calculations.
   - Install `requests` for HTTP requests.

3. **Configure the Trading Bot**:
   - **Timeframe**: Configurable by the user (e.g., 1h, 4h).
   - **Position Size**: Configurable, with a default of 100 USD margin.
   - **Leverage**: Configurable, with a default of 3x.
   - **Position Type**: Configurable, with a default of isolated.
   - **Coin Selection**: Choose the trading pair (e.g., BTC/USDT).

## Implementation

### Strategy Overview

The strategy involves the following steps:
1. Calculate SMA 21 and EMA 34 bands.
2. Monitor for price closures outside these bands.
3. Open a position on the next candle's opening after the price closes outside the band.
4. Set take-profit and stop-loss levels based on the band's position and configurable percentages.

### Calculating SMA 21 and EMA 34 Bands

To calculate the SMA and EMA bands, fetch historical OHLC data using the Blofin API and use `pandas` for computations.
python
import pandas as pd
from blofin import Client

# Initialize the client
client = Client(api_key='your_api_key', api_secret='your_api_secret')

# Fetch historical candlestick data
symbol = 'BTC/USDT'
timeframe = '1h'
data = client.get_klines(symbol=symbol, interval=timeframe)

# Convert to DataFrame
df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume'])

# Calculate SMA 21 and EMA 34
df['SMA_21'] = df['close'].rolling(21).mean()
df['EMA_34'] = df['close'].ewm(span=34, adjust=False).mean()

# Calculate the band's upper and lower bounds
df['Upper_Band'] = df['SMA_21'] + 2*df['SMA_21'].rolling(21).std()
df['Lower_Band'] = df['SMA_21'] - 2*df['SMA_21'].rolling(21).std()


### Monitoring Price Closures Outside the Bands

Monitor real-time data for price closures outside the bands using Websocket connections for efficient data retrieval.
python
import websockets
import json

async def monitor_price_closures():
    async with websockets.connect('wss://stream.blofin.com/ws') as websocket:
        await websocket.send(json.dumps({
            "method": "SUBSCRIBE",
            "params": [f"binance:{symbol}:1h"],
            "id": 1
        }))
        
        while True:
            data = await websocket.recv()
            data = json.loads(data)
            
            if data['k']['x']:
                close_price = float(data['k']['c'])
                if close_price > df['Upper_Band'].iloc[-1]:
                    # Price closed above the upper band
                    print("Price closed above the upper band")
                elif close_price < df['Lower_Band'].iloc[-1]:
                    # Price closed below the lower band
                    print("Price closed below the lower band")


### Opening Positions on the Next Candle's Opening

Use scheduling libraries or server time synchronization to open positions precisely at the opening of the next candle.
python
import schedule
import time

def open_position():
    # Check if the price closed outside the bands
    if close_price > upper_band:
        # Open a long position
        client.place_order(symbol=symbol, side='BUY', type='MARKET', quantity=calculate_position_size())
    elif close_price < lower_band:
        # Open a short position
        client.place_order(symbol=symbol, side='SELL', type='MARKET', quantity=calculate_position_size())

schedule.every().hour.at(":00").do(open_position)  # Run at the start of each hour


### Setting Take-Profit and Stop-Loss Levels

For short positions, set the stop-loss above the band (highest wick of the last 10 candles). For long positions, set the stop-loss below the band (lowest wick of the last 10 candles). The take-profit is set at a configurable percentage from the entry point.
python
def setriskmanagement(symbol, side, quantity, entry_price, tp_percent, sl_percent):
    # Set take-profit
    tp_price = entry_price * (1 + tp_percent/100) if side == 'BUY' else entry_price * (1 - tp_percent/100)
    client.place_order(symbol=symbol, side='SELL' if side == 'BUY' else 'BUY', type='TAKE_PROFIT', quantity=quantity, stop_price=tp_price)

    # Set stop-loss
    sl_price = entry_price * (1 - sl_percent/100) if side == 'BUY' else entry_price * (1 + sl_percent/100)
    client.place_order(symbol=symbol, side='SELL' if side == 'BUY' else 'BUY', type='STOP_LOSS', quantity=quantity, stop_price=sl_price)


## Risk Management

### Position Sizing

The position size is configurable, with a default of 100 USD margin. The contract size is adjusted to ensure the position size matches the specified margin amount.
python
def calculate_position_size(symbol, margin, entry_price):
    # Calculate the position size based on margin and entry price
    position_size = margin / (entry_price * 0.001)  # Assuming 0.1% margin
    return position_size


### Configurable Parameters

- **Timeframe**: Choose the desired timeframe (e.g., 1h, 4h).
- **Position Size**: Configure the margin size (default is 100 USD).
- **Leverage**: Set the leverage (default is 3x).
- **Position Type**: Choose between isolated or cross margin (default is isolated).
- **Coin Selection**: Select the trading pair (e.g., BTC/USDT).

## Testing and Optimization

### Backtesting

Backtest the strategy on historical data to evaluate performance.

### Forward Testing

Test the strategy in the Blofin Demo environment to refine parameters before deploying it in a live trading environment.
python
def backtest_strategy(data, symbol, timeframe, margin, leverage):
    # Implement backtesting logic here
    pass

def forward_test_strategy(symbol, timeframe, margin, leverage):
    # Implement forward testing logic here
    pass


## Deployment and Monitoring

### Deployment

After testing and refining the strategy, deploy the bot in a live trading environment.

### Monitoring

Monitor the bot's performance using logging and alerting mechanisms. Handle potential issues like API limits and ensure robust implementation.

## Conclusion

This documentation provides a comprehensive guide to implementing a trading strategy using SMA 21 and EMA 34 bands with a Blofin Demo account and Python. The strategy involves opening positions based on price closures outside the bands and setting configurable take-profit and stop-loss levels. By following this guide, users can successfully implement and test the strategy using the provided code examples and resources.

---

## References

[1] Blofin Python SDK (GitHub)  
[2] Public API Methods Example (GitHub)  
[3] Trading API Methods Example (GitHub)  
[4] Account API Methods Example (GitHub)  
[5] User API Methods Example (GitHub)  
[6] Affiliate API Methods Example (GitHub)  
[7] Blofin Python SDK README (GitHub)