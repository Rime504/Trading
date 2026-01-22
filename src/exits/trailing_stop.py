"""
Trailing Stop Manager
Let winners run, cut losers quick
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TrailingStopManager:
    """Manage trailing stops to maximize winners"""
    
    def __init__(self):
        # R-multiple thresholds for trailing
        self.breakeven_threshold = 1.0  # Move to BE at 1R
        self.trail_start_threshold = 1.5  # Start trailing at 1.5R
        self.trail_distance = 0.5  # Trail 0.5R behind
        
        logger.info("🎯 Trailing Stop Manager initialized")
    
    def calculate_stop(self, signal: Dict, current_price: float) -> Dict:
        """
        Calculate current stop based on P&L
        
        Returns:
            {
                'stop_loss': float,
                'reason': str,
                'profit_locked': float
            }
        """
        entry = signal['entry']
        original_stop = signal['stop_loss']
        target = signal['target']
        direction = signal['direction']
        risk = signal['risk']
        
        # Calculate current P&L in R-multiples
        if direction == 'SHORT':
            current_pl = entry - current_price
            r_multiple = current_pl / risk if risk > 0 else 0
        else:  # LONG
            current_pl = current_price - entry
            r_multiple = current_pl / risk if risk > 0 else 0
        
        # RULE 1: Move to breakeven at 1R
        if r_multiple >= self.breakeven_threshold:
            if direction == 'SHORT':
                new_stop = entry  # Breakeven
            else:
                new_stop = entry
            
            return {
                'stop_loss': new_stop,
                'reason': 'BREAKEVEN',
                'profit_locked': 0.0,
                'r_multiple': r_multiple
            }
        
        # RULE 2: Trail stop at 1.5R
        if r_multiple >= self.trail_start_threshold:
            profit_to_lock = (r_multiple - self.trail_distance) * risk
            
            if direction == 'SHORT':
                new_stop = entry - profit_to_lock
            else:
                new_stop = entry + profit_to_lock
            
            return {
                'stop_loss': new_stop,
                'reason': 'TRAILING',
                'profit_locked': profit_to_lock,
                'r_multiple': r_multiple
            }
        
        # Default: Use original stop
        return {
            'stop_loss': original_stop,
            'reason': 'ORIGINAL',
            'profit_locked': 0.0,
            'r_multiple': r_multiple
        }
    
    def should_take_profit(self, signal: Dict, current_price: float) -> tuple[bool, str]:
        """
        Check if should take profit
        
        Returns:
            (should_exit, reason)
        """
        entry = signal['entry']
        target = signal['target']
        direction = signal['direction']
        risk = signal['risk']
        
        # Calculate R-multiple
        if direction == 'SHORT':
            current_pl = entry - current_price
            r_multiple = current_pl / risk if risk > 0 else 0
            
            # Target hit
            if current_price <= target:
                return True, f"TARGET_HIT_{r_multiple:.1f}R"
            
        else:  # LONG
            current_pl = current_price - entry
            r_multiple = current_pl / risk if risk > 0 else 0
            
            # Target hit
            if current_price >= target:
                return True, f"TARGET_HIT_{r_multiple:.1f}R"
        
        # RULE: Take profit at 3R if not hit target yet (don't be greedy)
        if r_multiple >= 3.0:
            return True, "3R_PROFIT_LOCK"
        
        return False, "HOLD"