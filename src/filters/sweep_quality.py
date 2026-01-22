"""
Sweep Quality Scorer
Not all liquidity sweeps are created equal
"""

import logging
from typing import List, Dict
from datetime import datetime, time

logger = logging.getLogger(__name__)


class SweepQualityScorer:
    """Score liquidity sweep quality (0-10 scale)"""
    
    def __init__(self):
        self.overnight_session_start = time(17, 0)
        self.overnight_session_end = time(9, 30)
    
    def score_sweep(self, sweep_data: Dict, bars: List[Dict]) -> float:
        """Score sweep quality 0.0-10.0"""
        score = 5.0  # Baseline
        swept_level = sweep_data['swing_level']
        
        # Check if swept level is significant
        
        # 1. Is it overnight high/low? (+3 points)
        if self._is_overnight_extreme(swept_level, bars):
            score += 3.0
            logger.debug(f"   +3: Overnight extreme swept")
        
        # 2. Is it previous day's high/low? (+2 points)
        if self._is_previous_day_extreme(swept_level, bars):
            score += 2.0
            logger.debug(f"   +2: Previous day extreme swept")
        
        # 3. How clean is the sweep? (+1 point)
        if self._is_clean_sweep(sweep_data):
            score += 1.0
            logger.debug(f"   +1: Clean sweep")
        
        score = min(score, 10.0)
        
        logger.info(f"Sweep Quality Score: {score:.1f}/10")
        return score
    
    def _is_overnight_extreme(self, level: float, bars: List[Dict]) -> bool:
        """Check if level is overnight session high/low"""
        for bar in bars[-100:]:
            bar_time = bar['time']
            if isinstance(bar_time, str):
                try:
                    bar_time = datetime.fromisoformat(bar_time.replace('Z', '+00:00')).time()
                except:
                    continue
            elif isinstance(bar_time, datetime):
                bar_time = bar_time.time()
            else:
                continue
            
            if (bar_time >= self.overnight_session_start or 
                bar_time <= self.overnight_session_end):
                
                if abs(bar['high'] - level) < 10 or abs(bar['low'] - level) < 10:
                    return True
        
        return False
    
    def _is_previous_day_extreme(self, level: float, bars: List[Dict]) -> bool:
        """Check if level is previous day's high/low"""
        if len(bars) < 156:
            return False
        
        prev_day_bars = bars[-156:-78]
        prev_day_high = max([b['high'] for b in prev_day_bars])
        prev_day_low = min([b['low'] for b in prev_day_bars])
        
        if abs(level - prev_day_high) < 5 or abs(level - prev_day_low) < 5:
            return True
        
        return False
    
    def _is_clean_sweep(self, sweep_data: Dict) -> bool:
        """Check if sweep was clean"""
        if sweep_data['type'] == 'buyside_sweep':
            wick_size = abs(sweep_data['sweep_high'] - sweep_data['close'])
            return wick_size > 5
        elif sweep_data['type'] == 'sellside_sweep':
            wick_size = abs(sweep_data['sweep_low'] - sweep_data['close'])
            return wick_size > 5
        
        return False