"""
Position Sizing Calculator
Based on MNQ formula from your PDF + risk percentage
"""

import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv('config/secrets.env')

logger = logging.getLogger(__name__)


class PositionSizer:
    """Calculate position size based on risk and instrument"""
    
    def __init__(self, account_size: float, risk_per_trade: float = 0.005):
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
        self.max_risk_dollars = account_size * risk_per_trade
        
        # MNQ position sizing from PDF (points of risk → contracts)
        self.mnq_brackets = {
            (20, 24): 5,
            (25, 30): 4,
            (31, 40): 3,
            (41, 60): 2,
            (60, 120): 1,
        }
        
        logger.info(f"Position Sizer initialized: ${account_size} account, "
                   f"{risk_per_trade*100}% risk (${self.max_risk_dollars} max)")
    
    def calculate_position_size(self, symbol: str, entry: float, stop: float, 
                                tick_value: float = 2.0, min_tick: float = 0.25) -> Dict:
        """
        Calculate position size based on risk
        
        Args:
            symbol: Instrument symbol (MNQ, ES, NQ)
            entry: Entry price
            stop: Stop loss price
            tick_value: Dollar value per tick (MNQ = $2, ES = $50, NQ = $20)
            min_tick: Minimum tick size (usually 0.25)
            
        Returns:
            Dict with position size, risk in dollars, contracts
        """
        # Calculate risk in points
        risk_points = abs(entry - stop)
        
        # Calculate risk in ticks
        risk_ticks = risk_points / min_tick
        
        # Calculate risk in dollars per contract
        risk_per_contract = risk_ticks * tick_value
        
        # Calculate number of contracts based on max risk
        contracts_by_risk = int(self.max_risk_dollars / risk_per_contract)
        
        # For MNQ, also check bracket sizing
        if symbol == 'MNQ':
            contracts_by_bracket = self._get_mnq_contracts(risk_points)
            # Use more conservative (smaller) size
            contracts = min(contracts_by_risk, contracts_by_bracket)
        else:
            contracts = contracts_by_risk
        
        # Ensure at least 1 contract
        contracts = max(1, contracts)
        
        # Calculate actual risk with this position size
        actual_risk_dollars = contracts * risk_per_contract
        
        # Calculate potential reward
        # (Will be filled in by signal generator with target)
        
        result = {
            'symbol': symbol,
            'contracts': contracts,
            'entry': entry,
            'stop': stop,
            'risk_points': risk_points,
            'risk_per_contract': risk_per_contract,
            'total_risk_dollars': actual_risk_dollars,
            'risk_percentage': (actual_risk_dollars / self.account_size) * 100,
            'tick_value': tick_value,
        }
        
        logger.info(f"Position Size: {contracts} contracts, "
                   f"Risk: ${actual_risk_dollars:.2f} ({result['risk_percentage']:.2f}%)")
        
        return result
    
    def _get_mnq_contracts(self, risk_points: float) -> int:
        """Get MNQ contract size based on PDF brackets"""
        for (min_points, max_points), contracts in self.mnq_brackets.items():
            if min_points <= risk_points <= max_points:
                logger.debug(f"MNQ bracket: {risk_points:.1f} points = {contracts} contracts")
                return contracts
        
        # If outside brackets, use 1 contract (safest)
        logger.warning(f"Risk points {risk_points:.1f} outside brackets, using 1 contract")
        return 1
    
    def validate_position(self, position_size_data: Dict) -> bool:
        """Validate position doesn't exceed risk limits"""
        if position_size_data['total_risk_dollars'] > self.max_risk_dollars * 1.1:
            logger.error(f"Position risk ${position_size_data['total_risk_dollars']:.2f} "
                        f"exceeds max ${self.max_risk_dollars:.2f}")
            return False
        
        if position_size_data['contracts'] < 1:
            logger.error("Position size is 0 contracts")
            return False
        
        return True
    
    def update_account_size(self, new_size: float):
        """Update account size (e.g., after profits/losses)"""
        self.account_size = new_size
        self.max_risk_dollars = new_size * self.risk_per_trade
        logger.info(f"Account updated: ${new_size:.2f}, Max risk: ${self.max_risk_dollars:.2f}")