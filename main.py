"""
Main Execution File - Run This to Start the System
Monitors market during NY session (9:30-11:00 AM EST)
"""

import asyncio
import logging
from datetime import datetime, time
import pytz
import sys
import os
from dotenv import load_dotenv
from src.trade_logger import TradeLogger

# Add src to path
sys.path.append(os.path.dirname(__file__))

from config import settings
from src.data.ib_data_feed import IBDataFeed
from src.strategy.signal_generator import SignalGenerator
from src.risk.position_sizing import PositionSizer
from src.alerts.discord_bot import DiscordAlerter

# Load environment
load_dotenv('config/secrets.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ConfirmationModelSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("CONFIRMATION MODEL ALGO - INITIALIZING")
        logger.info("=" * 60)
        
        # Initialize components
        self.data_feed = IBDataFeed()
        self.signal_generator = SignalGenerator(settings.__dict__)
        self.trade_logger = TradeLogger()
        
        # Get account size from env or use default
        account_size = float(os.getenv('ACCOUNT_SIZE', 50000))
        risk_per_trade = float(os.getenv('RISK_PER_TRADE', 0.005))
        
        self.position_sizer = PositionSizer(account_size, risk_per_trade)
        self.discord = DiscordAlerter()
        
        # Trading state
        self.is_trading = False
        self.signals_today = []
        self.trades_today = 0
        
        # Timezone
        self.tz = pytz.timezone(settings.TIMEZONE)
        
        logger.info("✅ All components initialized")
    
    async def start(self):
        """Start the system"""
        logger.info("🚀 System starting...")
        
        # Connect to Interactive Brokers
        connected = await self.data_feed.connect()
        if not connected:
            logger.error("❌ Failed to connect to IB. Exiting.")
            return
        
        # Subscribe to instruments
        primary = settings.PRIMARY_INSTRUMENT
        await self.data_feed.subscribe_instrument(
            primary,
            settings.INSTRUMENTS[primary]['exchange']
        )
        
        # Get historical data for initialization
        logger.info("📊 Loading historical data...")
        historical = await self.data_feed.get_historical_bars(
            primary,
            duration='2 D',
            bar_size='1 min'
        )
        
        if not historical:
            logger.error("❌ Could not load historical data")
            return
        
        logger.info(f"✅ Loaded {len(historical)} historical bars")
        
        # Send startup message
        self.discord.send_system_message(
            f"🚀 **System Started** - Monitoring {primary} during NY session (9:30-11:00 AM EST)"
        )
        
        # Main monitoring loop
        await self.monitoring_loop(primary, historical)
    
    async def monitoring_loop(self, symbol: str, historical_bars: list):
        """Main monitoring loop"""
        logger.info("👀 Monitoring loop started")
        
        ltf_bars = historical_bars.copy()  # 1-min bars
        htf_bars_15m = []  # Will aggregate to 15-min
        htf_bars_1h = []   # Will aggregate to 1-hour
        
        last_check_time = None
        
        while True:
            try:
                # Get current time in EST
                now = datetime.now(self.tz)
                current_time = now.time()
                
                # Check if we're in trading hours
                trading_start = time(9, 30)
                trading_end = time(11, 0)
                
                if trading_start <= current_time <= trading_end:
                    if not self.is_trading:
                        logger.info("✅ MARKET OPEN - Trading session started")
                        self.discord.send_system_message("🔔 **NY Session Open** - Monitoring for setups")
                        self.is_trading = True
                    
                    # Get latest bars from data feed
                    latest_bars = self.data_feed.bars_data.get(symbol, [])
                    
                    if latest_bars:
                        # Update LTF bars
                        ltf_bars.extend(latest_bars)
                        ltf_bars = ltf_bars[-500:]  # Keep last 500 bars
                        
                        # Aggregate to HTF (simplified - in production, use proper aggregation)
                        htf_bars_15m = self._aggregate_bars(ltf_bars, 15)
                        htf_bars_1h = self._aggregate_bars(ltf_bars, 60)
                        
                        # Check for signals (only once per minute)
                        current_minute = now.replace(second=0, microsecond=0)
                        if last_check_time != current_minute:
                            last_check_time = current_minute
                            
                            signal = self.signal_generator.check_for_signal(
                                ltf_bars,
                                htf_bars_15m,
                                min_tick=settings.INSTRUMENTS[symbol]['min_tick']
                            )
                            
                            if signal:
                                await self.handle_signal(signal, symbol)
                    
                    # Wait before next check
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                elif current_time >= trading_end:
                    if self.is_trading:
                        logger.info("🔔 MARKET CLOSE - Trading session ended")
                        self.discord.send_daily_summary(self.signals_today, 0.0)
                        self.is_trading = False
                        
                        # Reset for next day
                        self.signals_today = []
                        self.trades_today = 0
                    
                    # Wait until next trading day
                    logger.info("⏸️  Outside trading hours - waiting...")
                    await asyncio.sleep(60)  # Check every minute
                    
                else:
                    # Before market open
                    if not self.is_trading:
                        minutes_until_open = ((trading_start.hour * 60 + trading_start.minute) - 
                                            (current_time.hour * 60 + current_time.minute))
                        if minutes_until_open <= 30:
                            logger.info(f"⏰ Market opens in {minutes_until_open} minutes")
                    
                    await asyncio.sleep(60)
                    
            except KeyboardInterrupt:
                logger.info("⚠️  Keyboard interrupt - shutting down")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(10)
        
        # Cleanup
        self.data_feed.disconnect()
        logger.info("System shut down")
    
    async def handle_signal(self, signal: dict, symbol: str):
        """Handle signal generation"""
        logger.info("=" * 60)
        logger.info("🚨 SIGNAL DETECTED")
        logger.info("=" * 60)
        
        # Check if we've hit max trades for today
        if self.trades_today >= settings.MAX_TRADES_PER_DAY:
            logger.warning(f"⚠️  Max trades ({settings.MAX_TRADES_PER_DAY}) reached for today")
            return
        
        # Calculate position size
        position_size = self.position_sizer.calculate_position_size(
            symbol,
            signal['entry'],
            signal['stop_loss'],
            tick_value=settings.INSTRUMENTS[symbol]['tick_value'],
            min_tick=settings.INSTRUMENTS[symbol]['min_tick']
        )
        
        # Validate position
        if not self.position_sizer.validate_position(position_size):
            logger.error("❌ Position validation failed")
            return
        
        # Check risk/reward ratio
        if signal['risk_reward_ratio'] < settings.MIN_RISK_REWARD:
            logger.warning(f"⚠️  R:R {signal['risk_reward_ratio']:.1f} below minimum {settings.MIN_RISK_REWARD}")
            return
        
        # Send Discord alert
        success = self.discord.send_signal_alert(signal, position_size, symbol)
        
        if success:
            self.signals_today.append(signal)
            self.trades_today += 1
            logger.info(f"✅ Alert sent - Trade {self.trades_today}/{settings.MAX_TRADES_PER_DAY}")
        else:
            logger.error("❌ Failed to send alert")
    
    def _aggregate_bars(self, bars_1m: list, timeframe_minutes: int) -> list:
        """Aggregate 1-min bars to higher timeframe"""
        if len(bars_1m) < timeframe_minutes:
            return []
        
        aggregated = []
        i = 0
        
        while i < len(bars_1m):
            chunk = bars_1m[i:i+timeframe_minutes]
            if len(chunk) == timeframe_minutes:
                agg_bar = {
                    'time': chunk[0]['time'],
                    'open': chunk[0]['open'],
                    'high': max(b['high'] for b in chunk),
                    'low': min(b['low'] for b in chunk),
                    'close': chunk[-1]['close'],
                    'volume': sum(b['volume'] for b in chunk),
                }
                aggregated.append(agg_bar)
            i += timeframe_minutes
        
        return aggregated


async def main():
    """Entry point"""
    system = ConfirmationModelSystem()
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")