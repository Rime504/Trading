"""
Market Structure Position Filter
Only trade at range extremes
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class StructureFilter:
    """Filter based on position within market structure"""
    
    def __init__(self, lookback_bars: int = 78):
        self.lookback_bars = lookback_bars
        
        # For SHORTS: Only at top 30% of range
        self.short_min_position = 0.70
        
        # For LONGS: Only at bottom 30% of range
        self.long_max_position = 0.30
        
        logger.info(f"📊 Structure Filter: Range extremes only")
    
    def calculate_range_position(self, entry_price: float, 
                                 bars: List[Dict]) -> Optional[float]:
        """Calculate where entry price sits in recent range"""
        if len(bars) < self.lookback_bars:
            logger.warning("Not enough bars for structure filter")
            return None
        
        recent_bars = bars[-self.lookback_bars:]
        
        range_high = max([b['high'] for b in recent_bars])
        range_low = min([b['low'] for b in recent_bars])
        
        range_size = range_high - range_low
        
        if range_size == 0:
            return 0.5
        
        position = (entry_price - range_low) / range_size
        
        return position
    
    def is_at_extreme(self, direction: str, entry_price: float, 
                     bars: List[Dict]) -> tuple:
        """Check if entry is at range extreme"""
        position = self.calculate_range_position(entry_price, bars)
        
        if position is None:
            return False, "INSUFFICIENT_DATA", 0.0
        
        if direction == 'SHORT':
            if position >= self.short_min_position:
                return True, f"SHORT_AT_EXTREME_TOP", position
            else:
                return False, f"SHORT_TOO_LOW_IN_RANGE", position
        
        elif direction == 'LONG':
            if position <= self.long_max_position:
                return True, f"LONG_AT_EXTREME_BOTTOM", position
            else:
                return False, f"LONG_TOO_HIGH_IN_RANGE", position
        
        return False, "UNKNOWN_DIRECTION", position
    
    def get_quality_score(self, direction: str, entry_price: float,
                         bars: List[Dict]) -> float:
        """Get quality score 0.0-1.0 based on structure position"""
        position = self.calculate_range_position(entry_price, bars)
        
        if position is None:
            return 0.0
        
        if direction == 'SHORT':
            if position >= self.short_min_position:
                normalized = (position - self.short_min_position) / (1.0 - self.short_min_position)
                return 0.7 + (normalized * 0.3)
            else:
                return 0.0
        
        elif direction == 'LONG':
            if position <= self.long_max_position:
                normalized = (self.long_max_position - position) / self.long_max_position
                return 0.7 + (normalized * 0.3)
            else:
                return 0.0
        
        return 0.0