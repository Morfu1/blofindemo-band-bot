import pandas as pd
import numpy as np
from typing import Tuple, Dict

class TradingStrategy:
    def __init__(self, sma_period: int, ema_period: int):
        self.sma_period = sma_period
        self.ema_period = ema_period

    def calculate_bands(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Calculate SMA and EMA bands"""
        data['SMA'] = data['close'].rolling(window=self.sma_period).mean()
        data['EMA'] = data['close'].ewm(span=self.ema_period, adjust=False).mean()
        
        return data['SMA'].iloc[-1], data['EMA'].iloc[-1]

    def get_signal(self, data: pd.DataFrame) -> Dict:
        """Generate trading signal based on band strategy"""
        sma, ema = self.calculate_bands(data)
        current_price = data['close'].iloc[-1]
        
        signal = {
            'action': None,
            'entry_price': None,
            'tp_price': None,
            'sl_price': None
        }

        if current_price > max(sma, ema):
            signal['action'] = 'long'
            signal['entry_price'] = current_price
            signal['tp_price'] = current_price * 1.02  # 2% TP
            signal['sl_price'] = min(sma, ema) * 0.99  # 1% below band
            
        elif current_price < min(sma, ema):
            signal['action'] = 'short'
            signal['entry_price'] = current_price
            signal['tp_price'] = current_price * 0.98  # 2% TP
            signal['sl_price'] = max(sma, ema) * 1.01  # 1% above band

        return signal

    def should_scale_position(self, data: pd.DataFrame, position_type: str) -> bool:
        """Determine if position should be scaled"""
        sma, ema = self.calculate_bands(data)
        current_price = data['close'].iloc[-1]
        
        if position_type == 'long' and current_price <= min(sma, ema):
            return True
        elif position_type == 'short' and current_price >= max(sma, ema):
            return True
            
        return False

    def calculate_new_tp(self, positions: list) -> float:
        """Calculate new TP based on average entry price"""
        total_size = sum(pos['size'] for pos in positions)
        avg_entry = sum(pos['size'] * pos['entry_price'] for pos in positions) / total_size
        
        return avg_entry * 1.02  # 2% from average entry
