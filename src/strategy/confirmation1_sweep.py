"""
Confirmation #1: Liquidity Sweep Detection
Identifies when price sweeps swing highs/lows and reverses
"""

import logging
from typing import List, Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class LiquiditySweepDetector:
    """Detects liquidity sweeps at swing highs and lows"""
    
    def __init__(self, min_swing_candles: int = 3, sweep_buffer_ticks: int = 1):
        self.min_swing_candles = min_swing_candles
        self.sweep_buffer_ticks = sweep_buffer_ticks
        self.swing_highs = []
        self.swing_lows = []
        
    def identify_swings(self, bars: List[Dict], lookback: int = 20) -> Tuple[List[Dict], List[Dict]]:
        """
        Identify swing highs and swing lows
        
        Swing High: High point with lower highs on both sides
        Swing Low: Low point with higher lows on both sides
        """
        if len(bars) < lookback:
            return [], []
        
        df = pd.DataFrame(bars)
        swing_highs = []
        swing_lows = []
        
        for i in range(self.min_swing_candles, len(df) - self.min_swing_candles):
            # Check for swing high
            is_swing_high = True
            current_high = df.iloc[i]['high']
            
            # Check left side
            for j in range(i - self.min_swing_candles, i):
                if df.iloc[j]['high'] >= current_high:
                    is_swing_high = False
                    break
            
            # Check right side
            if is_swing_high:
                for j in range(i + 1, i + self.min_swing_candles + 1):
                    if df.iloc[j]['high'] >= current_high:
                        is_swing_high = False
                        break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'time': df.iloc[i]['time'],
                    'price': current_high,
                    'type': 'swing_high'
                })
            
            # Check for swing low
            is_swing_low = True
            current_low = df.iloc[i]['low']
            
            # Check left side
            for j in range(i - self.min_swing_candles, i):
                if df.iloc[j]['low'] <= current_low:
                    is_swing_low = False
                    break
            
            # Check right side
            if is_swing_low:
                for j in range(i + 1, i + self.min_swing_candles + 1):
                    if df.iloc[j]['low'] <= current_low:
                        is_swing_low = False
                        break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'time': df.iloc[i]['time'],
                    'price': current_low,
                    'type': 'swing_low'
                })
        
        self.swing_highs = swing_highs
        self.swing_lows = swing_lows
        
        logger.info(f"Identified {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")
        return swing_highs, swing_lows
    
    def detect_sweep(self, current_bar: Dict, previous_bars: List[Dict], 
                     min_tick: float = 0.25) -> Optional[Dict]:
        """
        Detect if current price action swept a swing level
        
        Returns:
            Dict with sweep details if detected, None otherwise
        """
        # Get most recent swing levels
        if not self.swing_highs and not self.swing_lows:
            self.identify_swings(previous_bars)
        
        if not self.swing_highs and not self.swing_lows:
            return None
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Check for buyside liquidity sweep (sweep above swing high)
        if self.swing_highs:
            latest_swing_high = self.swing_highs[-1]
            swing_high_price = latest_swing_high['price']
            sweep_threshold = swing_high_price + (self.sweep_buffer_ticks * min_tick)
            
            # Did we sweep above the swing high?
            if current_high >= sweep_threshold:
                # Did we close back below it? (reversal confirmation)
                if current_close < swing_high_price:
                    logger.info(f"✅ BUYSIDE LIQUIDITY SWEEP detected at {swing_high_price}")
                    return {
                        'type': 'buyside_sweep',
                        'swing_level': swing_high_price,
                        'sweep_high': current_high,
                        'close': current_close,
                        'time': current_bar['time'],
                        'direction': 'SHORT',  # Expecting downward move
                    }
        
        # Check for sellside liquidity sweep (sweep below swing low)
        if self.swing_lows:
            latest_swing_low = self.swing_lows[-1]
            swing_low_price = latest_swing_low['price']
            sweep_threshold = swing_low_price - (self.sweep_buffer_ticks * min_tick)
            
            # Did we sweep below the swing low?
            if current_low <= sweep_threshold:
                # Did we close back above it? (reversal confirmation)
                if current_close > swing_low_price:
                    logger.info(f"✅ SELLSIDE LIQUIDITY SWEEP detected at {swing_low_price}")
                    return {
                        'type': 'sellside_sweep',
                        'swing_level': swing_low_price,
                        'sweep_low': current_low,
                        'close': current_close,
                        'time': current_bar['time'],
                        'direction': 'LONG',  # Expecting upward move
                    }
        
        return None
    
    def get_liquidity_levels(self) -> Dict:
        """Get current buy-side and sell-side liquidity levels"""
        buyside = [sh['price'] for sh in self.swing_highs[-5:]] if self.swing_highs else []
        sellside = [sl['price'] for sl in self.swing_lows[-5:]] if self.swing_lows else []
        
        return {
            'buyside_liquidity': buyside,
            'sellside_liquidity': sellside,
        }