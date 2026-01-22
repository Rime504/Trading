"""
Time-Based Edge Filter
First 30 mins of NY session = highest edge window
"""

import logging
from datetime import time, datetime
import pytz

logger = logging.getLogger(__name__)


class TimeFilter:
    """Filter trades based on time of day edge"""
    
    def __init__(self, timezone: str = "America/New_York"):
        self.tz = pytz.timezone(timezone)
        
        # CRITICAL: First 30 mins = best liquidity + most stops
        self.optimal_start = time(9, 30)
        self.optimal_end = time(10, 0)
        
        # Extended acceptable window
        self.acceptable_start = time(9, 30)
        self.acceptable_end = time(11, 0)
        
        logger.info(f"⏰ Time Filter: Optimal {self.optimal_start}-{self.optimal_end}")
    
    def is_optimal_time(self, signal_time) -> tuple:
        """Check if signal is in optimal time window"""
        # Handle different time formats
        if isinstance(signal_time, str):
            try:
                signal_time = datetime.fromisoformat(signal_time.replace('Z', '+00:00'))
            except:
                return False, "INVALID_TIME_FORMAT"
        
        if isinstance(signal_time, datetime):
            if signal_time.tzinfo is None:
                signal_time = self.tz.localize(signal_time)
            else:
                signal_time = signal_time.astimezone(self.tz)
            current_time = signal_time.time()
        else:
            return False, "INVALID_TIME_TYPE"
        
        # Check optimal window
        if self.optimal_start <= current_time <= self.optimal_end:
            return True, "OPTIMAL_WINDOW"
        
        # Check acceptable window
        if self.acceptable_start <= current_time <= self.acceptable_end:
            return True, "ACCEPTABLE_WINDOW"
        
        return False, "OUTSIDE_HOURS"
    
    def get_quality_multiplier(self, signal_time) -> float:
        """Get quality multiplier based on time"""
        is_optimal, reason = self.is_optimal_time(signal_time)
        
        if not is_optimal:
            return 0.0
        
        if reason == "OPTIMAL_WINDOW":
            return 1.0
        elif reason == "ACCEPTABLE_WINDOW":
            return 0.7
        
        return 0.0