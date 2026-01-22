"""
Confirmation #4: CISD (Change in State of Delivery)
Confirms structure break after iFVG inversion
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CISDDetector:
    """Detects Change in State of Delivery (structure break)"""
    
    def detect_cisd(self, bars: List[Dict], sweep_data: Dict, 
                    direction: str) -> Optional[Dict]:
        """
        Detect CISD - structure break confirmation
        
        After liquidity sweep, identify the series of candles leading into it,
        then confirm price closes through the first candle's open
        """
        if len(bars) < 10:
            return None
        
        sweep_time = sweep_data['time']
        
        # Find the sweep candle in bars
        sweep_index = None
        for i, bar in enumerate(bars):
            if bar['time'] == sweep_time:
                sweep_index = i
                break
        
        if sweep_index is None or sweep_index < 5:
            return None
        
        if direction == 'SHORT':
            # Find series of UP-CLOSE candles before the sweep
            up_close_series = []
            for i in range(sweep_index - 1, max(0, sweep_index - 10), -1):
                bar = bars[i]
                if bar['close'] > bar['open']:  # Up-close candle
                    up_close_series.append(bar)
                else:
                    break  # Stop at first down-close
            
            if not up_close_series:
                return None
            
            # Get the FIRST up-close candle (furthest back)
            first_candle = up_close_series[-1]
            cisd_level = first_candle['open']
            
            # Check if current price closed BELOW this level
            current_bar = bars[-1]
            if current_bar['close'] < cisd_level:
                logger.info(f"✅ CISD CONFIRMED (SHORT) - Closed below {cisd_level}")
                return {
                    'cisd_level': cisd_level,
                    'direction': 'SHORT',
                    'first_candle': first_candle,
                    'current_close': current_bar['close'],
                    'time': current_bar['time'],
                }
        
        elif direction == 'LONG':
            # Find series of DOWN-CLOSE candles before the sweep
            down_close_series = []
            for i in range(sweep_index - 1, max(0, sweep_index - 10), -1):
                bar = bars[i]
                if bar['close'] < bar['open']:  # Down-close candle
                    down_close_series.append(bar)
                else:
                    break  # Stop at first up-close
            
            if not down_close_series:
                return None
            
            # Get the FIRST down-close candle (furthest back)
            first_candle = down_close_series[-1]
            cisd_level = first_candle['open']
            
            # Check if current price closed ABOVE this level
            current_bar = bars[-1]
            if current_bar['close'] > cisd_level:
                logger.info(f"✅ CISD CONFIRMED (LONG) - Closed above {cisd_level}")
                return {
                    'cisd_level': cisd_level,
                    'direction': 'LONG',
                    'first_candle': first_candle,
                    'current_close': current_bar['close'],
                    'time': current_bar['time'],
                }
        
        return None