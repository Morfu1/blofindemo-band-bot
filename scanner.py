import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict
from strategy import TradingStrategy

class CoinScanner:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.strategy = TradingStrategy(config.SMA_PERIOD, config.EMA_PERIOD)
        self.last_scan_time = None
        self.monitored_coins = []
        self.MIN_VOLUME_USDT = 500000  # Lowered to 500K USDT for testing

    def get_monitored_coins(self) -> List[Dict]:
        """Get currently monitored coins with their signals"""
        try:
            top_coins = self.get_top_volume_coins()
            monitored_coins = []

            for symbol in top_coins:
                try:
                    data = self.exchange.fetch_ohlcv(symbol, self.config.TIMEFRAME)
                    signal = self.strategy.get_signal(data)
                    volume = data['volume'].iloc[-1] if not data.empty else 0

                    coin_info = {
                        'symbol': symbol,
                        'volume': volume,
                        'signal': signal['action'] if signal['action'] else None
                    }
                    monitored_coins.append(coin_info)
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {str(e)}")
                    continue

            monitored_coins.sort(key=lambda x: x['volume'], reverse=True)
            return monitored_coins

        except Exception as e:
            self.logger.error(f"Error in get_monitored_coins: {str(e)}")
            return []

    def get_top_volume_coins(self) -> List[str]:
        """Get top volume coins from the exchange with strict volume validation"""
        try:
            # Fetch all available USDT pairs
            markets = self.exchange.exchange.fetch_markets()
            usdt_pairs = [
                market['symbol'] for market in markets 
                if market['quote'] == 'USDT' and market['active']
            ]

            self.logger.info(f"\n=== Volume Scanning Process ===")
            self.logger.info(f"Found {len(usdt_pairs)} active USDT pairs")
            self.logger.info(f"Volume threshold: {self.MIN_VOLUME_USDT:,.0f} USDT")

            # Fetch 24h volume for each pair with strict validation
            volumes = []
            pairs_processed = 0
            pairs_with_volume = 0

            for pair in usdt_pairs:
                try:
                    pairs_processed += 1
                    ticker = self.exchange.exchange.fetch_ticker(pair)

                    # Debug log for ticker data
                    self.logger.debug(f"Raw ticker data for {pair}: {ticker}")

                    # Try different volume fields that Blofin might use
                    volume = None
                    volume_fields = ['quoteVolume', 'baseVolume', 'volume', 'volumeUsd']

                    for field in volume_fields:
                        if field in ticker and ticker[field] is not None:
                            volume = ticker[field]
                            self.logger.debug(f"Found volume in field: {field}")
                            break

                    if volume is None:
                        self.logger.info(f"❌ {pair}: No valid volume field found in ticker data")
                        continue

                    try:
                        volume_usdt = float(volume)
                    except (ValueError, TypeError):
                        self.logger.info(f"❌ {pair}: Invalid volume format")
                        continue

                    if volume_usdt <= 0:
                        self.logger.info(f"❌ {pair}: Zero or negative volume")
                        continue

                    pairs_with_volume += 1

                    if volume_usdt < self.MIN_VOLUME_USDT:
                        self.logger.info(f"❌ {pair}: {volume_usdt:,.2f} USDT (Below threshold)")
                        continue

                    volumes.append({
                        'symbol': pair,
                        'volume': volume_usdt
                    })
                    self.logger.info(f"✅ {pair}: {volume_usdt:,.2f} USDT")

                except Exception as e:
                    self.logger.info(f"❌ Error processing {pair}: {str(e)}")
                    continue

            # Sort by volume and get top N pairs
            volumes.sort(key=lambda x: x['volume'], reverse=True)
            top_pairs = [v['symbol'] for v in volumes[:self.config.TOP_COINS_TO_SCAN]]

            # Log scanning summary
            self.logger.info("\n=== Scanning Summary ===")
            self.logger.info(f"Total pairs processed: {pairs_processed}")
            self.logger.info(f"Pairs with valid volume: {pairs_with_volume}")
            self.logger.info(f"Pairs above threshold: {len(volumes)}")

            if volumes:
                self.logger.info("\n=== Selected Monitoring Pairs ===")
                for v in volumes[:self.config.TOP_COINS_TO_SCAN]:
                    self.logger.info(f"🔍 {v['symbol']}: {v['volume']:,.2f} USDT")
            else:
                self.logger.info("No pairs met the volume criteria")

            self.logger.info("===============================")

            self.monitored_coins = top_pairs
            return top_pairs

        except Exception as e:
            self.logger.error(f"Error in get_top_volume_coins: {str(e)}")
            return []

    def scan_for_opportunities(self, active_positions: List[Dict]) -> List[Dict]:
        """Scan top volume coins for trading opportunities"""
        opportunities = []
        active_symbols = [pos['symbol'] for pos in active_positions]

        # Don't scan if we already have max positions
        if len(active_positions) >= self.config.MAX_POSITIONS:
            self.logger.info(f"Already at maximum positions ({self.config.MAX_POSITIONS})")
            return []

        current_time = datetime.now().strftime("%H:%M:%S")
        self.logger.info(f"\n=== Starting scan at {current_time} ===")
        self.logger.info(f"Active positions: {len(active_positions)} of {self.config.MAX_POSITIONS}")

        top_coins = self.get_top_volume_coins()
        self.logger.info(f"Scanning {len(top_coins)} pairs for opportunities:")
        for v in top_coins:
            self.logger.info(f"- {v}")
        self.logger.info("================================")

        for symbol in top_coins:
            # Skip if we already have a position in this symbol
            if symbol in active_symbols:
                self.logger.debug(f"Skipping {symbol} - already have an active position")
                continue

            try:
                # Get OHLCV data for the symbol
                data = self.exchange.fetch_ohlcv(symbol, self.config.TIMEFRAME)
                if data.empty:
                    continue

                # Check for trading signals
                signal = self.strategy.get_signal(data)

                if signal['action']:
                    self.logger.info(f"Found {signal['action']} opportunity for {symbol}")
                    opportunities.append({
                        'symbol': symbol,
                        'signal': signal,
                        'volume': data['volume'].iloc[-1]
                    })

            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue

        # Sort opportunities by volume
        opportunities.sort(key=lambda x: x['volume'], reverse=True)

        # Return only enough opportunities to reach MAX_POSITIONS
        slots_available = self.config.MAX_POSITIONS - len(active_positions)
        return opportunities[:slots_available]