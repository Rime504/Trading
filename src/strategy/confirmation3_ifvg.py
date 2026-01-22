"""
Confirmation #3: iFVG (Inverse Fair Value Gap) Detection
Identifies FVG inversions on lower timeframes (1-5 min)
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class iFVGDetector:
    """Detects FVG inversions on lower timeframes"""
    
    def __init__(self, min_fvg_size_ticks: int = 1):
        self.min_fvg_size_ticks = min_fvg_size_ticks
        self.recent_fvgs = []
        
    def detect_ifvg_inversion(self, bars: List[Dict], direction: str, 
                             min_tick: float = 0.25) -> Optional[Dict]:
        """
        Detect iFVG inversion
        
        Inversion = FVG forms, then price CLOSES THROUGH the opposite side
        (opposite of HTF FVG where we want respect)
        
        For SHORTS: Look for bullish FVG that gets disrespected (closed below)
        For LONGS: Look for bearish FVG that gets disrespected (closed above)
        """
        if len(bars) < 4:
            return None
        
        # Look at last 4 bars for FVG + inversion
        recent = bars[-4:]
        
        if direction == 'SHORT':
            # Looking for bullish FVG that gets disrespected
            for i in range(len(recent) - 3):
                c1 = recent[i]
                c2 = recent[i + 1]
                c3 = recent[i + 2]
                c4 = recent[i + 3]  # Inversion candle
                
                # Check for bullish FVG
                bullish_gap_bottom = c1['low']
                bullish_gap_top = c3['high']
                gap_size = bullish_gap_top - bullish_gap_bottom
                
                # Is there a gap?
                if (c2['low'] > bullish_gap_bottom and 
                    c2['high'] < bullish_gap_top and
                    gap_size >= self.min_fvg_size_ticks * min_tick):
                    
                    # Does the next candle close BELOW the FVG? (disrespect)
                    if c4['close'] < bullish_gap_bottom:
                        logger.info(f"✅ iFVG INVERSION (SHORT) - Bullish FVG disrespected")
                        return {
                            'type': 'bullish_fvg_disrespected',
                            'fvg_top': bullish_gap_top,
                            'fvg_bottom': bullish_gap_bottom,
                            'inversion_close': c4['close'],
                            'inversion_time': c4['time'],
                            'direction': 'SHORT',
                        }
        
        elif direction == 'LONG':
            # Looking for bearish FVG that gets disrespected
            for i in range(len(recent) - 3):
                c1 = recent[i]
                c2 = recent[i + 1]
                c3 = recent[i + 2]
                c4 = recent[i + 3]  # Inversion candle
                
                # Check for bearish FVG
                bearish_gap_top = c1['high']
                bearish_gap_bottom = c3['low']
                gap_size = bearish_gap_top - bearish_gap_bottom
                
                # Is there a gap?
                if (c2['high'] < bearish_gap_top and 
                    c2['low'] > bearish_gap_bottom and
                    gap_size >= self.min_fvg_size_ticks * min_tick):
                    
                    # Does the next candle close ABOVE the FVG? (disrespect)
                    if c4['close'] > bearish_gap_top:
                        logger.info(f"✅ iFVG INVERSION (LONG) - Bearish FVG disrespected")
                        return {
                            'type': 'bearish_fvg_disrespected',
                            'fvg_top': bearish_gap_top,
                            'fvg_bottom': bearish_gap_bottom,
                            'inversion_close': c4['close'],
                            'inversion_time': c4['time'],
                            'direction': 'LONG',
                        }
        
        return None
    
    def check_stacked_fvgs(self, bars: List[Dict], direction: str, 
                          min_tick: float = 0.25) -> bool:
        """
        Check if multiple FVGs are stacked (from your PDF note)
        All stacked FVGs must be disrespected
        """
        # Simplified implementation - in production, track all FVGs properly
        # For now, basic inversion check handles this
        return True