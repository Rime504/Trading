"""
Signal Generator with RELAXED FILTERS for backtesting
"""

import logging
from typing import Optional, Dict, List
from .confirmation1_sweep import LiquiditySweepDetector
from .confirmation2_htf_fvg import HTFFVGDetector
from .confirmation3_ifvg import iFVGDetector
from .confirmation4_cisd import CISDDetector

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Only import filters if not disabled
FILTERS_ENABLED = os.environ.get('DISABLE_FILTERS', 'false').lower() != 'true'

if FILTERS_ENABLED:
    from filters.time_filter import TimeFilter
    from filters.volatility_filter import VolatilityFilter
    from filters.structure_filter import StructureFilter
    from filters.sweep_quality import SweepQualityScorer

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trading signals with optional filters"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize confirmations
        self.sweep_detector = LiquiditySweepDetector(
            min_swing_candles=config.get('MIN_SWING_CANDLES', 3),
            sweep_buffer_ticks=config.get('SWEEP_BUFFER_TICKS', 1)
        )
        
        self.htf_fvg_detector = HTFFVGDetector(
            min_fvg_size_ticks=config.get('MIN_FVG_SIZE_TICKS', 2),
            max_age=config.get('MAX_HTF_FVG_AGE', 20)
        )
        
        self.ifvg_detector = iFVGDetector(min_fvg_size_ticks=1)
        self.cisd_detector = CISDDetector()
        
        # Initialize filters (if enabled)
        self.filters_enabled = FILTERS_ENABLED and config.get('USE_EDGE_FILTERS', True)
        
        if self.filters_enabled:
            try:
                self.time_filter = TimeFilter()
                self.volatility_filter = VolatilityFilter(max_vix=config.get('MAX_VIX_LEVEL', 25))
                self.structure_filter = StructureFilter()
                self.sweep_scorer = SweepQualityScorer()
                logger.info("🎯 Signal Generator initialized WITH edge filters")
            except Exception as e:
                logger.warning(f"Could not initialize filters: {e}")
                self.filters_enabled = False
        
        if not self.filters_enabled:
            logger.info("🎯 Signal Generator initialized WITHOUT filters (baseline mode)")
        
        # Confirmation state
        self.confirmation_state = {
            'sweep': None,
            'htf_fvg': None,
            'ifvg': None,
            'cisd': None,
        }
        
        # Relaxed filter thresholds for backtesting
        self.min_sweep_quality = config.get('MIN_SWEEP_QUALITY', 5.0)  # Lowered from 7.0
        self.min_overall_score = config.get('MIN_OVERALL_SCORE', 0.5)  # Lowered from 0.7
        
    def check_for_signal(self, ltf_bars: List[Dict], htf_bars: List[Dict], 
                        min_tick: float = 0.25) -> Optional[Dict]:
        """Check if all 4 confirmations pass (+ optional filters)"""
        if len(ltf_bars) < 20 or len(htf_bars) < 20:
            return None
        
        current_ltf_bar = ltf_bars[-1]
        
        # ========================================
        # CONFIRMATION #1: LIQUIDITY SWEEP
        # ========================================
        sweep = self.sweep_detector.detect_sweep(current_ltf_bar, ltf_bars[:-1], min_tick)
        
        if sweep:
            self.confirmation_state['sweep'] = sweep
            logger.info(f"[1/4] ✅ Liquidity Sweep: {sweep['type']}")
        
        if not self.confirmation_state['sweep']:
            return None
        
        direction = self.confirmation_state['sweep']['direction']
        
        # ========================================
        # CONFIRMATION #2: HTF FVG DELIVERY
        # ========================================
        if not self.confirmation_state['htf_fvg']:
            self.htf_fvg_detector.update_fvgs(htf_bars, min_tick)
            htf_delivery = self.htf_fvg_detector.check_delivery(
                self.htf_fvg_detector.active_fvgs, current_ltf_bar
            )
            
            if htf_delivery and htf_delivery['direction'] == direction:
                self.confirmation_state['htf_fvg'] = htf_delivery
                logger.info(f"[2/4] ✅ HTF FVG Delivery: {htf_delivery['fvg']['type']}")
        
        if not self.confirmation_state['htf_fvg']:
            return None
        
        # ========================================
        # CONFIRMATION #3: iFVG INVERSION
        # ========================================
        if not self.confirmation_state['ifvg']:
            ifvg_inversion = self.ifvg_detector.detect_ifvg_inversion(
                ltf_bars[-10:], direction, min_tick
            )
            
            if ifvg_inversion and ifvg_inversion['direction'] == direction:
                self.confirmation_state['ifvg'] = ifvg_inversion
                logger.info(f"[3/4] ✅ iFVG Inversion: {ifvg_inversion['type']}")
        
        if not self.confirmation_state['ifvg']:
            return None
        
        # ========================================
        # CONFIRMATION #4: CISD
        # ========================================
        if not self.confirmation_state['cisd']:
            cisd = self.cisd_detector.detect_cisd(ltf_bars, self.confirmation_state['sweep'], direction)
            
            if cisd and cisd['direction'] == direction:
                self.confirmation_state['cisd'] = cisd
                logger.info(f"[4/4] ✅ CISD: Structure broken at {cisd['cisd_level']:.2f}")
        
        if not self.confirmation_state['cisd']:
            return None
        
        # ALL 4 CONFIRMATIONS ALIGNED
        logger.info("🚨 All 4 confirmations aligned!")
        
        entry_price = current_ltf_bar['close']
        
        # ========================================
        # OPTIONAL: RUN EDGE FILTERS
        # ========================================
        if self.filters_enabled:
            filter_result = self._run_edge_filters(current_ltf_bar, direction, entry_price, ltf_bars)
            if filter_result is None:
                self._reset_confirmation_state()
                return None
            
            time_score, vol_score, structure_score, sweep_quality, vix = filter_result
        else:
            # No filters, default scores
            time_score = 1.0
            vol_score = 1.0
            structure_score = 1.0
            sweep_quality = 10.0
            vix = 15.0
        
        # BUILD SIGNAL
        signal = self._build_signal(current_ltf_bar, direction, min_tick)
        
        if signal:
            signal['filter_scores'] = {
                'time_score': time_score,
                'volatility_score': vol_score,
                'structure_score': structure_score,
                'sweep_quality': sweep_quality,
                'overall_score': (time_score + vol_score + structure_score) / 3.0,
                'vix': vix,
                'filters_enabled': self.filters_enabled
            }
        
        self._reset_confirmation_state()
        return signal
    
    def _run_edge_filters(self, current_bar, direction, entry_price, ltf_bars):
        """Run all edge filters, return scores or None if failed"""
        
        # FILTER 1: TIME (relaxed for backtest)
        is_good_time, time_reason = self.time_filter.is_optimal_time(current_bar['time'])
        time_score = self.time_filter.get_quality_multiplier(current_bar['time'])
        
        # For backtest: Don't fail on time, just warn
        if not is_good_time:
            logger.warning(f"⚠️  TIME WARNING: {time_reason} (continuing anyway)")
            time_score = 0.5  # Reduced quality but not failed
        else:
            logger.info(f"✅ Time Filter: {time_reason} (score: {time_score:.2f})")
        
        # FILTER 2: VOLATILITY (relaxed)
        is_good_vol, vol_reason, vix = self.volatility_filter.is_favorable_volatility()
        vol_score = self.volatility_filter.get_quality_multiplier()
        
        # For backtest: Don't fail on vol in historical data
        if not is_good_vol:
            logger.warning(f"⚠️  VOL WARNING: {vol_reason} VIX={vix:.1f} (continuing anyway)")
            vol_score = 0.5
        else:
            logger.info(f"✅ Volatility Filter: {vol_reason} VIX={vix:.1f} (score: {vol_score:.2f})")
        
        # FILTER 3: STRUCTURE (this one we keep strict)
        is_at_extreme, structure_reason, position = self.structure_filter.is_at_extreme(
            direction, entry_price, ltf_bars
        )
        structure_score = self.structure_filter.get_quality_score(direction, entry_price, ltf_bars)
        
        if not is_at_extreme:
            logger.warning(f"❌ STRUCTURE FILTER FAILED: {structure_reason} (position: {position:.2%})")
            return None  # This one we fail on
        
        logger.info(f"✅ Structure Filter: {structure_reason} at {position:.2%} (score: {structure_score:.2f})")
        
        # FILTER 4: SWEEP QUALITY (relaxed)
        sweep_quality = self.sweep_scorer.score_sweep(self.confirmation_state['sweep'], ltf_bars)
        
        if sweep_quality < self.min_sweep_quality:
            logger.warning(f"⚠️  SWEEP WARNING: Quality {sweep_quality:.1f}/10 (continuing anyway)")
        else:
            logger.info(f"✅ Sweep Quality: {sweep_quality:.1f}/10")
        
        return time_score, vol_score, structure_score, sweep_quality, vix
    
    def _build_signal(self, current_bar: Dict, direction: str, min_tick: float) -> Dict:
        """Build complete signal"""
        sweep_level = self.confirmation_state['sweep']['swing_level']
        entry_price = current_bar['close']
        
        if direction == 'SHORT':
            stop_loss = sweep_level + (self.config.get('STOP_LOSS_BUFFER_TICKS', 3) * min_tick)
            target = self._find_opposing_liquidity(direction)
        else:
            stop_loss = sweep_level - (self.config.get('STOP_LOSS_BUFFER_TICKS', 3) * min_tick)
            target = self._find_opposing_liquidity(direction)
        
        risk = abs(entry_price - stop_loss)
        reward = abs(target - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        return {
            'time': current_bar['time'],
            'direction': direction,
            'entry': entry_price,
            'stop_loss': stop_loss,
            'target': target,
            'risk': risk,
            'reward': reward,
            'risk_reward_ratio': risk_reward,
            'confirmations': self.confirmation_state.copy(),
        }
    
    def _find_opposing_liquidity(self, direction: str) -> float:
        """Find opposing liquidity for target"""
        liquidity = self.sweep_detector.get_liquidity_levels()
        
        if direction == 'SHORT':
            if liquidity['sellside_liquidity']:
                return min(liquidity['sellside_liquidity'])
            else:
                return self.confirmation_state['sweep']['swing_level'] - (
                    abs(self.confirmation_state['sweep']['swing_level'] - 
                        self.confirmation_state['sweep']['close']) * 2
                )
        else:
            if liquidity['buyside_liquidity']:
                return max(liquidity['buyside_liquidity'])
            else:
                return self.confirmation_state['sweep']['swing_level'] + (
                    abs(self.confirmation_state['sweep']['swing_level'] - 
                        self.confirmation_state['sweep']['close']) * 2
                )
    
    def _reset_confirmation_state(self):
        """Reset confirmation state"""
        self.confirmation_state = {
            'sweep': None,
            'htf_fvg': None,
            'ifvg': None,
            'cisd': None,
        }