"""
Volatility Regime Filter
Mean reversion works in low vol, trend following in high vol
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VolatilityFilter:
    """Filter based on market volatility regime"""
    
    def __init__(self, max_vix: float = 20.0, cache_minutes: int = 60):
        self.max_vix = max_vix
        self.cache_minutes = cache_minutes
        
        self.cached_vix = None
        self.cache_time = None
        
        logger.info(f"📊 Volatility Filter: Max VIX = {max_vix}")
    
    def get_current_vix(self) -> Optional[float]:
        """Get current VIX level (with caching)"""
        now = datetime.now()
        
        # Use cache if fresh
        if (self.cached_vix is not None and 
            self.cache_time is not None and
            (now - self.cache_time).total_seconds() < self.cache_minutes * 60):
            return self.cached_vix
        
        try:
            import yfinance as yf
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="1d")
            
            if not vix_data.empty:
                current_vix = float(vix_data['Close'].iloc[-1])
                self.cached_vix = current_vix
                self.cache_time = now
                logger.debug(f"VIX: {current_vix:.2f}")
                return current_vix
            
        except Exception as e:
            logger.warning(f"Could not fetch VIX: {e}")
            return self.max_vix + 1
        
        return None
    
    def is_favorable_volatility(self) -> tuple:
        """Check if volatility regime is favorable"""
        vix = self.get_current_vix()
        
        if vix is None:
            return False, "VIX_UNAVAILABLE", 999.0
        
        if vix <= 15:
            return True, "LOW_VOL_OPTIMAL", vix
        elif vix <= self.max_vix:
            return True, "MODERATE_VOL_ACCEPTABLE", vix
        else:
            return False, "HIGH_VOL_UNFAVORABLE", vix
    
    def get_quality_multiplier(self) -> float:
        """Get quality multiplier based on volatility"""
        is_favorable, reason, vix = self.is_favorable_volatility()
        
        if not is_favorable:
            return 0.0
        
        if reason == "LOW_VOL_OPTIMAL":
            return 1.0
        elif reason == "MODERATE_VOL_ACCEPTABLE":
            return 0.7
        
        return 0.0