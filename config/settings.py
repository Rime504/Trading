"""
Confirmation Model - Strategy Settings with EDGE FILTERS
"""

# INSTRUMENTS
INSTRUMENTS = {
    'MNQ': {
        'symbol': 'MNQ',
        'exchange': 'CME',
        'currency': 'USD',
        'type': 'FUT',
        'tick_value': 2.0,
        'min_tick': 0.25,
    },
    'ES': {
        'symbol': 'ES',
        'exchange': 'CME',
        'currency': 'USD',
        'type': 'FUT',
        'tick_value': 50.0,
        'min_tick': 0.25,
    },
}

PRIMARY_INSTRUMENT = 'MNQ'

# TIMEFRAMES
HTF_TIMEFRAMES = ['15 mins', '1 hour']
LTF_TIMEFRAME = '1 min'

# TRADING HOURS
TRADING_START_TIME = "09:30"
TRADING_END_TIME = "11:00"
TIMEZONE = "America/New_York"

# === EDGE FILTERS (THE SECRET SAUCE) ===
MAX_VIX_LEVEL = 20  # Don't trade if VIX > 20
MIN_SWEEP_QUALITY = 7.0  # Minimum sweep score out of 10
MIN_OVERALL_SCORE = 0.7  # Minimum combined filter score

# RISK MANAGEMENT
RISK_PER_TRADE = 0.005
MAX_TRADES_PER_DAY = 2
MAX_DAILY_LOSS = 0.02
MIN_RISK_REWARD = 2.0

# POSITION SIZING
MNQ_POSITION_SIZING = {
    (20, 24): 5,
    (25, 30): 4,
    (31, 40): 3,
    (41, 60): 2,
    (60, 120): 1,
}

MAX_RISK_DOLLARS = 400  # Increased from 250

# CONFIRMATIONS
REQUIRE_LIQUIDITY_SWEEP = True
REQUIRE_HTF_FVG_DELIVERY = True
REQUIRE_IFVG_INVERSION = True
REQUIRE_CISD = True

# LIQUIDITY SWEEP
MIN_SWING_CANDLES = 3
SWEEP_BUFFER_TICKS = 1

# FVG
MIN_FVG_SIZE_TICKS = 2
MAX_HTF_FVG_AGE = 20

# STOPS
STOP_LOSS_BUFFER_TICKS = 3
USE_OPPOSING_LIQUIDITY = True

# ALERTS
ALERT_VALID_DURATION = 5
ENABLE_DISCORD = True

# LOGGING
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_FILE_PATH = "logs/system.log"

# BACKTESTING
BACKTEST_START_DATE = "2024-01-01"
BACKTEST_END_DATE = "2024-12-31"
BACKTEST_INITIAL_CAPITAL = 50000

# PERFORMANCE
AUTO_SAVE_TRADES = True
TRADE_LOG_PATH = "results/trade_log.csv"