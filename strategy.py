import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Optional

class TradingStrategy:
    def __init__(self, sma_period: int, ema_period: int):
        self.sma_period = sma_period
        self.ema_period = ema_period
        self.logger = logging.getLogger(__name__)

    def calculate_bands(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate SMA and EMA bands with validation"""
        if len(data) < max(self.sma_period, self.ema_period):
            raise ValueError(f"Not enough data points. Need at least {max(self.sma_period, self.ema_period)} points.")

        sma = data['close'].rolling(window=self.sma_period, min_periods=self.sma_period).mean()
        ema = data['close'].ewm(span=self.ema_period, adjust=False, min_periods=self.ema_period).mean()

        self.logger.info(f"Last SMA value: {sma.iloc[-1]:.2f}, Last EMA value: {ema.iloc[-1]:.2f}")
        return sma, ema

    def get_signal(self, data: pd.DataFrame) -> Dict:
        """Generate trading signal based on band strategy with improved validation"""
        if data.empty:
            return {'action': None, 'entry_price': None, 'tp_price': None, 'sl_price': None}

        sma, ema = self.calculate_bands(data)
        current_price = float(data['close'].iloc[-1])
        upper_band = max(sma.iloc[-1], ema.iloc[-1])
        lower_band = min(sma.iloc[-1], ema.iloc[-1])

        signal = {
            'action': None,
            'entry_price': None,
            'tp_price': None,
            'sl_price': None,
            'upper_band': upper_band,
            'lower_band': lower_band
        }

        self.logger.info(f"Current price: {current_price:.2f}, Upper band: {upper_band:.2f}, Lower band: {lower_band:.2f}")

        # Long signal: price closes above both bands
        if current_price > upper_band:
            signal.update({
                'action': 'long',
                'entry_price': current_price,
                'tp_price': current_price * 1.02,  # 2% TP
                'sl_price': lower_band * 0.99  # 1% below lower band
            })
            self.logger.info(f"Generated LONG signal - Entry: {current_price:.2f}, TP: {signal['tp_price']:.2f}, SL: {signal['sl_price']:.2f}")

        # Short signal: price closes below both bands
        elif current_price < lower_band:
            signal.update({
                'action': 'short',
                'entry_price': current_price,
                'tp_price': current_price * 0.98,  # 2% TP
                'sl_price': upper_band * 1.01  # 1% above upper band
            })
            self.logger.info(f"Generated SHORT signal - Entry: {current_price:.2f}, TP: {signal['tp_price']:.2f}, SL: {signal['sl_price']:.2f}")

        return signal

    def should_scale_position(self, data: pd.DataFrame, position_type: str) -> bool:
        """Determine if position should be scaled with improved logic"""
        if data.empty or position_type not in ['long', 'short']:
            return False

        sma, ema = self.calculate_bands(data)
        current_price = float(data['close'].iloc[-1])
        upper_band = max(sma.iloc[-1], ema.iloc[-1])
        lower_band = min(sma.iloc[-1], ema.iloc[-1])

        # Scale long position when price hits lower band
        if position_type == 'long' and current_price <= lower_band:
            self.logger.info(f"Scale opportunity for LONG position detected at price {current_price:.2f}")
            return True
        # Scale short position when price hits upper band
        elif position_type == 'short' and current_price >= upper_band:
            self.logger.info(f"Scale opportunity for SHORT position detected at price {current_price:.2f}")
            return True

        return False

    def calculate_new_tp(self, current_price: float, positions: list) -> float:
        """Calculate new TP based on average entry price with validation"""
        if not positions:
            return current_price * 1.02

        total_size = sum(float(pos['size']) for pos in positions)
        if total_size <= 0:
            return current_price * 1.02

        avg_entry = sum(float(pos['size']) * float(pos['entry_price']) for pos in positions) / total_size
        new_tp = avg_entry * 1.02  # 2% from average entry
        self.logger.info(f"Calculated new TP: {new_tp:.2f} based on average entry: {avg_entry:.2f}")
        return new_tp