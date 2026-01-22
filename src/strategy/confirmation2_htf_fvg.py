"""
Confirmation #2: Higher Timeframe FVG (Fair Value Gap) Detection
Identifies FVGs on 15-min and 1-hour charts, confirms delivery (rejection)
"""

import logging
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class HTFFVGDetector:
    """Detects and validates Higher Timeframe Fair Value Gaps"""
    
    def __init__(self, min_fvg_size_ticks: int = 2, max_age: int = 20):
        self.min_fvg_size_ticks = min_fvg_size_ticks
        self.max_age = max_age
        self.active_fvgs = []
        
    def identify_fvgs(self, bars: List[Dict], min_tick: float = 0.25) -> List[Dict]:
        """
        Identify FVGs in bar data
        
        FVG = 3-candle pattern where middle candle has no wick overlap
        with first and third candles
        """
        if len(bars) < 3:
            return []
        
        df = pd.DataFrame(bars)
        fvgs = []
        
        for i in range(len(df) - 2):
            candle1 = df.iloc[i]
            candle2 = df.iloc[i + 1]
            candle3 = df.iloc[i + 2]
            
            # Check for BEARISH FVG (for potential shorts)
            # Candle 1: Bullish, Candle 2: Large bearish, Candle 3: Bearish
            # Gap between candle1 high and candle3 low
            
            bearish_gap_top = candle1['high']
            bearish_gap_bottom = candle3['low']
            bearish_gap_size = bearish_gap_top - bearish_gap_bottom
            
            # Check if middle candle doesn't overlap
            if (candle2['high'] < bearish_gap_top and 
                candle2['low'] > bearish_gap_bottom and
                bearish_gap_size >= self.min_fvg_size_ticks * min_tick):
                
                fvgs.append({
                    'type': 'bearish',
                    'top': bearish_gap_top,
                    'bottom': bearish_gap_bottom,
                    'size': bearish_gap_size,
                    'start_index': i,
                    'start_time': candle1['time'],
                    'direction': 'SHORT',
                    'filled': False,
                    'age': 0,
                })
            
            # Check for BULLISH FVG (for potential longs)
            # Candle 1: Bearish, Candle 2: Large bullish, Candle 3: Bullish
            # Gap between candle1 low and candle3 high
            
            bullish_gap_bottom = candle1['low']
            bullish_gap_top = candle3['high']
            bullish_gap_size = bullish_gap_top - bullish_gap_bottom
            
            # Check if middle candle doesn't overlap
            if (candle2['low'] > bullish_gap_bottom and 
                candle2['high'] < bullish_gap_top and
                bullish_gap_size >= self.min_fvg_size_ticks * min_tick):
                
                fvgs.append({
                    'type': 'bullish',
                    'top': bullish_gap_top,
                    'bottom': bullish_gap_bottom,
                    'size': bullish_gap_size,
                    'start_index': i,
                    'start_time': candle1['time'],
                    'direction': 'LONG',
                    'filled': False,
                    'age': 0,
                })
        
        logger.info(f"Identified {len(fvgs)} HTF FVGs")
        return fvgs
    
    def check_delivery(self, fvgs: List[Dict], current_bar: Dict) -> Optional[Dict]:
        """
        Check if price has delivered into an FVG and rejected
        
        Delivery = Price taps into FVG zone and reverses (doesn't close through)
        """
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        for fvg in fvgs:
            if fvg['filled']:
                continue
            
            # Increment age
            fvg['age'] += 1
            
            # Invalidate if too old
            if fvg['age'] > self.max_age:
                fvg['filled'] = True
                continue
            
            # Check BEARISH FVG delivery (for shorts)
            if fvg['type'] == 'bearish':
                # Did price rally into the FVG?
                if current_high >= fvg['bottom']:
                    # Did it reject (close back below FVG)?
                    if current_close < fvg['bottom']:
                        logger.info(f"✅ BEARISH HTF FVG DELIVERY at {fvg['bottom']}-{fvg['top']}")
                        return {
                            'fvg': fvg,
                            'delivery_confirmed': True,
                            'delivery_time': current_bar['time'],
                            'direction': 'SHORT',
                        }
                    # Did it close through? (invalidates FVG)
                    elif current_close > fvg['top']:
                        fvg['filled'] = True
                        logger.info(f"❌ BEARISH FVG INVALIDATED (closed through)")
            
            # Check BULLISH FVG delivery (for longs)
            elif fvg['type'] == 'bullish':
                # Did price drop into the FVG?
                if current_low <= fvg['top']:
                    # Did it reject (close back above FVG)?
                    if current_close > fvg['top']:
                        logger.info(f"✅ BULLISH HTF FVG DELIVERY at {fvg['bottom']}-{fvg['top']}")
                        return {
                            'fvg': fvg,
                            'delivery_confirmed': True,
                            'delivery_time': current_bar['time'],
                            'direction': 'LONG',
                        }
                    # Did it close through? (invalidates FVG)
                    elif current_close < fvg['bottom']:
                        fvg['filled'] = True
                        logger.info(f"❌ BULLISH FVG INVALIDATED (closed through)")
        
        return None
    
    def update_fvgs(self, bars: List[Dict], min_tick: float = 0.25):
        """Update list of active FVGs"""
        new_fvgs = self.identify_fvgs(bars[-50:], min_tick)  # Look at recent 50 bars
        
        # Keep only unfilled FVGs
        self.active_fvgs = [fvg for fvg in new_fvgs if not fvg.get('filled', False)]
        
        logger.debug(f"Active HTF FVGs: {len(self.active_fvgs)}")