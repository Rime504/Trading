"""
Backtesting Engine for The Confirmation Model
Tests strategy on historical data to validate edge
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from typing import List, Dict

sys.path.append(os.path.dirname(__file__))

from config import settings
from src.strategy.signal_generator import SignalGenerator
from src.risk.position_sizing import PositionSizer


class Backtester:
    """Backtest the Confirmation Model strategy"""
    
    def __init__(self, symbol: str = 'MNQ', start_date: str = '2023-01-01', 
                 end_date: str = '2024-12-31', initial_capital: float = 50000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        print(f"🔧 Initializing backtester for {symbol}")
        self.signal_generator = SignalGenerator(settings.__dict__)
        self.position_sizer = PositionSizer(initial_capital)
        
        self.trades = []
        self.equity_curve = [initial_capital]
        self.daily_returns = []
        
    def download_data(self) -> pd.DataFrame:
        """Download historical data using local file or yfinance"""
        print(f"\n📊 Loading {self.symbol} data...")
        
        # Check for local IB data first
        local_file = 'data/MNQ_historical_30days.csv'
        if self.symbol == 'MNQ' and os.path.exists(local_file):
             print(f"   ✅ Found local data file: {local_file}")
             try:
                 df = pd.read_csv(local_file)
                 print(f"   ✅ Loaded {len(df)} bars from CSV")
                 # Ensure date column is parsed? 
                 # prepare_bars handles it as string or object usually, but let's see.
                 return df
             except Exception as e:
                 print(f"   ⚠️ Error loading local file: {e}")

        print(f"   ⬇️  Downloading from yfinance ({self.start_date} to {self.end_date})...")
        
        # Ticker mapping for Yahoo Finance
        ticker_map = {
            'MNQ': 'NQ=F',   # Micro Nasdaq futures
            'ES': 'ES=F',    # E-mini S&P futures
            'NQ': 'NQ=F'     # E-mini Nasdaq futures
        }
        
        ticker = ticker_map.get(self.symbol, self.symbol)
        
        try:
            import yfinance as yf
            
            # Try to get intraday data first (if available)
            print(f"   Attempting to download intraday data for {ticker}...")
            df = yf.download(ticker, start=self.start_date, end=self.end_date, 
                           interval='5m', progress=False)
            
            if df.empty or len(df) < 100:
                print("   ⚠️  Limited intraday data. Trying hourly...")
                df = yf.download(ticker, start=self.start_date, end=self.end_date, 
                               interval='1h', progress=False)
            
            if df.empty or len(df) < 100:
                print("   ⚠️  Using daily data for simulation...")
                df = yf.download(ticker, start=self.start_date, end=self.end_date, 
                               interval='1d', progress=False)
            
            if not df.empty:
                print(f"   ✅ Downloaded {len(df)} bars")
                return df
            else:
                print("   ❌ No data available")
                return pd.DataFrame()
            
        except ImportError:
            print("   ❌ yfinance not installed")
            print("   🔧 Fix: pip install yfinance")
            return pd.DataFrame()
        except Exception as e:
            print(f"   ❌ Error downloading data: {e}")
            return pd.DataFrame()
    
    def prepare_bars(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to bar format"""
        bars = []
        
        # Reset index to make sure we can access columns properly
        df_reset = df.reset_index()
        
        # Normalize column names to lowercase for checking
        for idx, row in df_reset.iterrows():
            try:
                # Helper to get value case-insensitively
                def get_val(keys, default=0.0):
                    for k in keys:
                        if k in row:
                            val = row[k]
                            return float(val) if pd.notna(val) else default
                        # Also check lowercase version if not found
                        if k.lower() in row:
                            val = row[k.lower()]
                            return float(val) if pd.notna(val) else default
                    return default
                
                # Get time
                time_val = row.get('Date', row.get('Datetime', row.get('date', idx)))
                if isinstance(time_val, pd.Timestamp):
                     time_val = time_val.isoformat()
                
                bars.append({
                    'time': time_val,
                    'open': get_val(['Open', 'open']),
                    'high': get_val(['High', 'high']),
                    'low': get_val(['Low', 'low']),
                    'close': get_val(['Close', 'close']),
                    'volume': get_val(['Volume', 'volume'])
                })
            except Exception as e:
                # Only print first few errors
                if idx < 5:
                    print(f"   ⚠️ Skipping bar {idx}: {e}")
                continue
    
        return bars
    
    def aggregate_to_timeframe(self, bars: List[Dict], periods: int) -> List[Dict]:
        """Aggregate bars to higher timeframe"""
        if len(bars) < periods:
            return bars  # Return original if not enough data
        
        aggregated = []
        
        for i in range(0, len(bars), periods):
            chunk = bars[i:i+periods]
            if len(chunk) > 0:
                agg_bar = {
                    'time': chunk[0]['time'],
                    'open': chunk[0]['open'],
                    'high': max(b['high'] for b in chunk),
                    'low': min(b['low'] for b in chunk),
                    'close': chunk[-1]['close'],
                    'volume': sum(b.get('volume', 0) for b in chunk)
                }
                aggregated.append(agg_bar)
        
        return aggregated
    
    def run_backtest(self):
        """Run the complete backtest"""
        print("\n" + "=" * 70)
        print("BACKTESTING THE CONFIRMATION MODEL")
        print("=" * 70)
        
        # Download data
        df = self.download_data()
        
        if df.empty:
            print("\n❌ Cannot run backtest without data")
            print("💡 Make sure you have internet connection and yfinance installed")
            print("   Run: pip install yfinance")
            return
        
        # Prepare bars
        print("\n🔄 Preparing data...")
        ltf_bars = self.prepare_bars(df)
        print(f"   ✅ Prepared {len(ltf_bars)} bars for analysis")
        
        # Create higher timeframe bars (simulate 15m and 1h)
        print("   🔄 Creating higher timeframe data...")
        htf_bars_15m = self.aggregate_to_timeframe(ltf_bars, 3)  # Approximate 15m from 5m
        htf_bars_1h = self.aggregate_to_timeframe(ltf_bars, 12)  # Approximate 1h from 5m
        
        print(f"   ✅ 15m bars: {len(htf_bars_15m)}")
        print(f"   ✅ 1h bars: {len(htf_bars_1h)}")
        
        # Run through bars looking for signals
        print(f"\n🔍 Scanning for Confirmation Model setups...")
        print("   This may take a few minutes...\n")
        
        signals_found = 0
        
        # Start from bar 100 to have enough history
        for i in range(100, len(ltf_bars)):
            # Progress indicator every 1000 bars
            if i % 1000 == 0:
                progress = (i / len(ltf_bars)) * 100
                print(f"   Progress: {progress:.1f}% ({i}/{len(ltf_bars)} bars)")
            
            # Get current data
            current_ltf = ltf_bars[:i+1]
            current_htf_15m = htf_bars_15m[:len(current_ltf)//3] if htf_bars_15m else current_ltf
            current_htf_1h = htf_bars_1h[:len(current_ltf)//12] if htf_bars_1h else current_ltf
            
            # Check for signal
            try:
                signal = self.signal_generator.check_for_signal(
                    current_ltf[-200:],  # Use last 200 bars for efficiency
                    current_htf_15m[-50:] if current_htf_15m else current_ltf[-200:],
                    min_tick=settings.INSTRUMENTS.get(self.symbol, settings.INSTRUMENTS['MNQ'])['min_tick']
                )
                
                if signal:
                    signals_found += 1
                    print(f"\n   🎯 Signal #{signals_found} found at {signal['time']}")
                    
                    # Calculate position size
                    position_size = self.position_sizer.calculate_position_size(
                        self.symbol,
                        signal['entry'],
                        signal['stop_loss'],
                        tick_value=settings.INSTRUMENTS.get(self.symbol, settings.INSTRUMENTS['MNQ'])['tick_value']
                    )
                    
                    # Validate
                    if self.position_sizer.validate_position(position_size):
                        # Simulate trade
                        result = self.simulate_trade(signal, position_size, ltf_bars[i:])
                        
                        if result:
                            self.trades.append(result)
                            self.capital += result['pnl']
                            self.equity_curve.append(self.capital)
                            
                            # Update position sizer with new capital
                            self.position_sizer.update_account_size(self.capital)
                            
                            win_loss = '✅ WIN' if result['pnl'] > 0 else '❌ LOSS' if result['pnl'] < 0 else '⚪ BE'
                            print(f"      {result['direction']} @ {result['entry']:.2f} → {win_loss} ${result['pnl']:.2f}")
            
            except Exception as e:
                # Continue on errors (don't stop entire backtest)
                if signals_found == 0 and i == 100:
                    print(f"   ⚠️  Error on first check: {e}")
                continue
        
        print(f"\n✅ Backtest complete! Found {signals_found} total signals")
        print(f"   Executed {len(self.trades)} trades\n")
        
        # Generate report
        if len(self.trades) > 0:
            self.generate_report()
        else:
            print("❌ No valid trades executed during backtest period")
            print("💡 This could mean:")
            print("   - Market conditions didn't trigger all 4 confirmations")
            print("   - Timeframe of data doesn't match strategy requirements")
            print("   - Try a longer date range or different symbol")
    
    def simulate_trade(self, signal: Dict, position_size: Dict, 
                      future_bars: List[Dict]) -> Dict:
        """Simulate trade outcome based on stop/target"""
        entry = signal['entry']
        stop = signal['stop_loss']
        target = signal['target']
        direction = signal['direction']
        
        # Look at next bars to see if stop or target hit first
        max_bars_to_check = min(100, len(future_bars))
        
        for bar in future_bars[:max_bars_to_check]:
            if direction == 'SHORT':
                # Check if stop hit (price goes up)
                if bar['high'] >= stop:
                    pnl = -position_size['total_risk_dollars']
                    return {
                        'time': signal['time'],
                        'direction': direction,
                        'entry': entry,
                        'exit': stop,
                        'pnl': pnl,
                        'result': 'LOSS',
                        'contracts': position_size['contracts'],
                        'bars_held': future_bars.index(bar) + 1
                    }
                
                # Check if target hit (price goes down)
                if bar['low'] <= target:
                    reward_dollars = position_size['contracts'] * (entry - target) * position_size['tick_value']
                    return {
                        'time': signal['time'],
                        'direction': direction,
                        'entry': entry,
                        'exit': target,
                        'pnl': reward_dollars,
                        'result': 'WIN',
                        'contracts': position_size['contracts'],
                        'bars_held': future_bars.index(bar) + 1
                    }
            
            else:  # LONG
                # Check if stop hit (price goes down)
                if bar['low'] <= stop:
                    pnl = -position_size['total_risk_dollars']
                    return {
                        'time': signal['time'],
                        'direction': direction,
                        'entry': entry,
                        'exit': stop,
                        'pnl': pnl,
                        'result': 'LOSS',
                        'contracts': position_size['contracts'],
                        'bars_held': future_bars.index(bar) + 1
                    }
                
                # Check if target hit (price goes up)
                if bar['high'] >= target:
                    reward_dollars = position_size['contracts'] * (target - entry) * position_size['tick_value']
                    return {
                        'time': signal['time'],
                        'direction': direction,
                        'entry': entry,
                        'exit': target,
                        'pnl': reward_dollars,
                        'result': 'WIN',
                        'contracts': position_size['contracts'],
                        'bars_held': future_bars.index(bar) + 1
                    }
        
        # If neither hit in max_bars, exit at breakeven
        return {
            'time': signal['time'],
            'direction': direction,
            'entry': entry,
            'exit': entry,
            'pnl': 0,
            'result': 'BREAKEVEN',
            'contracts': position_size['contracts'],
            'bars_held': max_bars_to_check
        }
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if len(self.trades) == 0:
            return
        
        # Calculate metrics
        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] < 0]
        breakeven = [t for t in self.trades if t['pnl'] == 0]
        
        total_trades = len(self.trades)
        total_pnl = sum(t['pnl'] for t in self.trades)
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losses]) if losses else 0
        
        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = sum(abs(t['pnl']) for t in losses)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        largest_win = max([t['pnl'] for t in self.trades])
        largest_loss = min([t['pnl'] for t in self.trades])
        
        # Sharpe Ratio
        returns = [(t['pnl'] / self.initial_capital) for t in self.trades]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Max Drawdown
        peak = self.initial_capital
        max_dd = 0
        max_dd_pct = 0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = peak - equity
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                max_dd = dd
        
        # Direction breakdown
        longs = [t for t in self.trades if t['direction'] == 'LONG']
        shorts = [t for t in self.trades if t['direction'] == 'SHORT']
        
        long_wins = len([t for t in longs if t['pnl'] > 0])
        short_wins = len([t for t in shorts if t['pnl'] > 0])
        
        long_pnl = sum([t['pnl'] for t in longs])
        short_pnl = sum([t['pnl'] for t in shorts])
        
        # Print report
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS - THE CONFIRMATION MODEL")
        print("=" * 70)
        
        print(f"\n📅 PERIOD: {self.start_date} → {self.end_date}")
        print(f"💰 STARTING CAPITAL: ${self.initial_capital:,.2f}")
        print(f"💰 ENDING CAPITAL: ${self.capital:,.2f}")
        print(f"📈 NET PROFIT: ${total_pnl:,.2f} ({(total_pnl/self.initial_capital)*100:+.2f}%)")
        
        print(f"\n🎯 TRADE STATISTICS:")
        print(f"   ├─ Total Signals: {total_trades}")
        print(f"   ├─ Wins: {len(wins)} ({win_rate:.1f}%)")
        print(f"   ├─ Losses: {len(losses)} ({(len(losses)/total_trades)*100:.1f}%)")
        print(f"   └─ Breakeven: {len(breakeven)} ({(len(breakeven)/total_trades)*100:.1f}%)")
        
        print(f"\n💵 PROFIT & LOSS:")
        print(f"   ├─ Gross Profit: ${gross_profit:,.2f}")
        print(f"   ├─ Gross Loss: ${gross_loss:,.2f}")
        print(f"   ├─ Average Win: ${avg_win:,.2f}")
        print(f"   ├─ Average Loss: ${avg_loss:,.2f}")
        print(f"   ├─ Largest Win: ${largest_win:,.2f}")
        print(f"   ├─ Largest Loss: ${largest_loss:,.2f}")
        print(f"   └─ Win/Loss Ratio: {(avg_win/avg_loss if avg_loss > 0 else 0):.2f}")
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"   ├─ Profit Factor: {profit_factor:.2f}")
        print(f"   ├─ Sharpe Ratio: {sharpe:.2f}")
        print(f"   ├─ Max Drawdown: ${max_dd:,.2f} ({max_dd_pct:.2f}%)")
        print(f"   ├─ Recovery Factor: {abs(total_pnl/max_dd) if max_dd > 0 else 0:.2f}")
        print(f"   └─ Expectancy: ${(total_pnl/total_trades):.2f} per trade")
        
        print(f"\n🎯 BY DIRECTION:")
        print(f"   ├─ LONG: {len(longs)} trades")
        print(f"   │   ├─ Win Rate: {(long_wins/len(longs)*100) if longs else 0:.1f}%")
        print(f"   │   └─ P&L: ${long_pnl:,.2f}")
        print(f"   └─ SHORT: {len(shorts)} trades")
        print(f"       ├─ Win Rate: {(short_wins/len(shorts)*100) if shorts else 0:.1f}%")
        print(f"       └─ P&L: ${short_pnl:,.2f}")
        
        # Save to CSV
        results_df = pd.DataFrame(self.trades)
        results_path = 'results/backtest_results.csv'
        results_df.to_csv(results_path, index=False)
        
        print(f"\n✅ Detailed results saved to: {results_path}")
        print("=" * 70)
        
        # Assessment
        print("\n📋 STRATEGY ASSESSMENT:")
        
        if win_rate >= 50 and profit_factor >= 1.5:
            print("   ✅ STRONG EDGE - Strategy shows positive expectancy")
        elif win_rate >= 40 and profit_factor >= 1.2:
            print("   ⚠️  MODERATE EDGE - Consider optimization")
        else:
            print("   ❌ WEAK EDGE - Strategy needs refinement")
        
        if max_dd_pct <= 15:
            print("   ✅ GOOD RISK CONTROL - Drawdown acceptable")
        elif max_dd_pct <= 25:
            print("   ⚠️  MODERATE RISK - Watch drawdowns carefully")
        else:
            print("   ❌ HIGH RISK - Reduce position sizes")
        
        if sharpe >= 1.5:
            print("   ✅ EXCELLENT SHARPE - Risk-adjusted returns strong")
        elif sharpe >= 1.0:
            print("   ⚠️  ADEQUATE SHARPE - Acceptable for futures")
        else:
            print("   ❌ LOW SHARPE - Returns don't justify risk")
        
        print("\n")


if __name__ == "__main__":
    print("🚀 Starting Confirmation Model Backtest\n")
    
    # Create backtester
    backtester = Backtester(
        symbol='MNQ',
        start_date='2024-01-01',  # 1 year (faster than 2 years)
        end_date='2024-12-31',
        initial_capital=50000
    )
    
    # Run backtest
    backtester.run_backtest()
    
    print("\n✅ Backtest complete! Check results/backtest_results.csv for details\n")