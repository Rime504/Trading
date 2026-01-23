# Confirmation Model Algo Trading System

**A semi-automated trading system for detecting high-probability setups using The Confirmation Model**

---

## 📖 Table of Contents

- [What This System Does](#-what-this-system-does)
- [Why This System Exists](#-why-this-system-exists)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Installation & Deployment](#-installation--deployment)
- [Configuration](#-configuration)
- [Running the System](#-running-the-system)
- [Backtesting](#-backtesting)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Trading Workflow](#-trading-workflow)
- [Important Notes](#️-important-notes)

---

## 🎯 What This System Does

This is a **semi-automated algorithmic trading system** that:

1. **Monitors live market data** from Interactive Brokers (IB) in real-time
2. **Detects high-probability trading setups** using The Confirmation Model (4 confirmations)
3. **Sends instant alerts** to Discord/Telegram when all 4 confirmations align
4. **Calculates precise entry, stop-loss, and target levels** with proper position sizing
5. **Allows manual execution** by a human trader (compliant with prop firm rules)

### Key Features:
- ✅ Real-time market monitoring during NY session (9:30-11:00 AM EST)
- ✅ Multi-timeframe analysis (1m, 5m, 15m, 1h)
- ✅ Automated signal detection with 4 confirmations
- ✅ Risk management with position sizing (0.5% risk per trade)
- ✅ Discord/Telegram notifications with trade details
- ✅ Backtesting engine to validate strategy performance
- ✅ Comprehensive logging and trade tracking

---

## 💡 Why This System Exists

### The Problem:
- Prop firms don't allow fully automated trading during challenges
- Manually watching charts 24/7 is exhausting and error-prone
- Missing high-probability setups costs money

### The Solution:
- **The algo does the heavy lifting**: Monitors markets, detects setups, calculates risk
- **You execute manually**: Receive alerts, verify setup, place trade in prop firm platform
- **Best of both worlds**: Automation + human oversight = compliant & profitable

### The Goal:
- Pass prop firm challenges ($25K → $50K → $100K → $200K)
- Get funded accounts
- Scale to multiple accounts
- Achieve consistent profitability

---

## 🔍 How It Works

### The Confirmation Model (4 Confirmations)

Every signal requires **ALL FOUR** confirmations to align:

#### 1. **Liquidity Sweep** (`confirmation1_sweep.py`)
- Price takes out a swing high (for shorts) or swing low (for longs)
- Then reverses direction
- Indicates smart money trapped retail traders

#### 2. **HTF FVG Delivery** (`confirmation2_htf_fvg.py`)
- Higher timeframe Fair Value Gap (15m or 1h) is respected
- Price rejects from the FVG zone
- Confirms institutional order flow direction

#### 3. **iFVG Inversion** (`confirmation3_ifvg.py`)
- Inverse Fair Value Gap (1-5m) is disrespected
- Price closes through the iFVG
- Signals momentum shift

#### 4. **CISD (Change in State of Delivery)** (`confirmation4_cisd.py`)
- Market structure breaks
- Price closes through the pre-sweep candle series
- Confirms trend reversal

### Signal Generation Process

```
Real-time Data → 4 Confirmations → Signal Generator → Position Sizer → Alert
```

1. **Data Feed**: IB TWS provides real-time 1-minute bars
2. **Multi-Timeframe Analysis**: System aggregates to 5m, 15m, 1h
3. **Confirmation Checks**: Each confirmation module analyzes price action
4. **Signal Generation**: If all 4 align, signal is created
5. **Risk Calculation**: Position sizer calculates contracts based on account size
6. **Alert Sent**: Discord/Telegram notification with all trade details

---

## 📋 Prerequisites

### Required Software:
1. **Python 3.10+** (3.11 or 3.12 recommended)
2. **Interactive Brokers TWS** (Trader Workstation) or IB Gateway
3. **IB Account** (paper trading or live)
4. **Discord** (for alerts) or Telegram

### Required Accounts:
- Interactive Brokers account (free paper trading available)
- Discord server with webhook access (free)
- Optional: Telegram bot token

### System Requirements:
- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Internet**: Stable connection for real-time data
- **Storage**: 500MB for project + data

---

## 🚀 Installation & Deployment

### Step 1: Clone/Download the Project

```bash
# If using Git
git clone <your-repo-url>
cd Kam_Algo

# Or download ZIP and extract to:
# C:\Users\hp\OneDrive\CR_CAPITAL\Kam_Algo
```

### Step 2: Create Virtual Environment

```bash
# Navigate to project folder
cd C:\Users\hp\OneDrive\CR_CAPITAL\Kam_Algo

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Dependencies include:**
- `ib_insync` - Interactive Brokers API
- `python-dotenv` - Environment variable management
- `python-telegram-bot` - Telegram notifications
- `requests` - Discord webhooks
- `pandas` - Data manipulation
- `numpy` - Numerical computations
- `pytz` - Timezone handling
- `yfinance` - Historical data (for backtesting)
- `backtrader` - Backtesting framework

### Step 4: Configure Environment Variables

Create/edit `config/secrets.env`:

```env
# Interactive Brokers Connection
IB_HOST=127.0.0.1
IB_PORT=7497              # 7497 for paper, 7496 for live
IB_CLIENT_ID=1

# Discord Webhook (get from Discord channel settings)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Account Settings
ACCOUNT_SIZE=50000        # Your account size in USD
RISK_PER_TRADE=0.005      # 0.5% risk per trade (conservative)
```

### Step 5: Set Up Interactive Brokers TWS

1. **Download TWS**: https://www.interactivebrokers.com/en/trading/tws.php
2. **Install and launch TWS**
3. **Log in** to your paper trading account (red "DEMO SYSTEM" banner)
4. **Enable API**:
   - File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Socket port: `7497` (paper) or `7496` (live)
   - Trusted IP addresses: `127.0.0.1`
   - Click "OK"
5. **Keep TWS running** while the algo is active

### Step 6: Set Up Discord Webhook

1. Open your Discord server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it (e.g., "Trading Alerts")
5. Select channel for alerts
6. Copy webhook URL
7. Paste into `config/secrets.env`

### Step 7: Create Required Directories

```bash
# Create directories for logs and results
mkdir logs
mkdir results
mkdir screenshots
```

---

## ⚙️ Configuration

### Trading Parameters (`config/settings.py`)

```python
# Instrument
PRIMARY_INSTRUMENT = 'MNQ'  # Micro Nasdaq futures
# Options: 'MNQ', 'MES' (Micro S&P), 'ES', 'NQ'

# Trading Hours (EST)
TRADING_START_TIME = "09:30"  # Market open
TRADING_END_TIME = "11:00"    # First 1.5 hours (highest volume)

# Timeframes
TIMEFRAME_1M = 1    # 1-minute bars
TIMEFRAME_5M = 5    # 5-minute bars
TIMEFRAME_15M = 15  # 15-minute bars
TIMEFRAME_1H = 60   # 1-hour bars

# Risk Management
DEFAULT_RISK_PERCENT = 0.005  # 0.5% per trade
MAX_DAILY_LOSS = 0.03         # 3% max daily loss
MAX_POSITION_SIZE = 10        # Max contracts per trade

# Confirmation Thresholds
SWEEP_LOOKBACK = 20           # Bars to check for swing points
FVG_MIN_SIZE = 5              # Minimum FVG size in ticks
CISD_STRUCTURE_BREAKS = 2     # Required structure breaks
```

### Adjusting Risk

**Conservative (recommended for challenges):**
```env
RISK_PER_TRADE=0.005  # 0.5%
```

**Moderate:**
```env
RISK_PER_TRADE=0.01   # 1.0%
```

**Aggressive (funded accounts only):**
```env
RISK_PER_TRADE=0.02   # 2.0%
```

### Changing Instruments

Edit `config/settings.py`:
```python
PRIMARY_INSTRUMENT = 'MES'  # Switch to Micro S&P 500
```

**Available instruments:**
- `MNQ` - Micro Nasdaq (recommended for beginners)
- `MES` - Micro S&P 500
- `NQ` - Nasdaq futures (larger contract)
- `ES` - S&P 500 futures (larger contract)

---

## 🏃 Running the System

### Live Trading Mode

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Ensure TWS is running and logged in

# 3. Run the main system
python main.py
```

**Expected output:**
```
[2026-01-22 09:25:00] ============================================================
[2026-01-22 09:25:00] CONFIRMATION MODEL ALGO - INITIALIZING
[2026-01-22 09:25:00] ============================================================
[2026-01-22 09:25:01] ✅ Connected to IB at 127.0.0.1:7497
[2026-01-22 09:25:02] ✅ Subscribed to MNQ real-time data
[2026-01-22 09:25:05] ✅ Loaded 1440 historical bars
[2026-01-22 09:25:05] 👀 Monitoring loop started
[2026-01-22 09:25:06] ⏰ Market opens in 4 minutes
[2026-01-22 09:30:00] 🔔 MARKET OPEN - Monitoring for signals...
```

### What Happens Next:

1. **System monitors** real-time price action
2. **Checks confirmations** every 1-minute bar
3. **When signal detected**:
   - Discord/Telegram alert sent instantly
   - Alert includes: entry, stop, target, position size, R:R ratio
   - Chart screenshot attached (if enabled)
4. **You verify and execute** the trade manually
5. **System continues monitoring** for next signal

### Stopping the System

Press `Ctrl+C` to stop gracefully:
```
[2026-01-22 11:00:00] 🛑 Trading session ended
[2026-01-22 11:00:01] System stopped by user
```

---

## 📊 Backtesting

### Why Backtest?

- Validate strategy performance on historical data
- Understand win rate, average R:R, drawdowns
- Optimize parameters before risking real money
- Build confidence in the system

### Running a Backtest

```bash
# Activate virtual environment
venv\Scripts\activate

# Run backtest
python backtest_main.py
```

**Backtest parameters** (edit in `backtest_main.py`):
```python
backtester = Backtester(
    symbol='MNQ',
    start_date='2024-01-01',  # Start date
    end_date='2024-12-31',    # End date
    initial_capital=50000     # Starting capital
)
```

### Backtest Output

Results saved to `results/backtest_results.csv`:
```
Date,Signal,Entry,Stop,Target,Outcome,PnL,Balance
2024-03-15,LONG,18500,18480,18540,WIN,+$200,50200
2024-03-18,SHORT,18600,18620,18560,WIN,+$200,50400
2024-03-22,LONG,18450,18430,18490,LOSS,-$100,50300
...
```

**Performance metrics:**
- Total trades
- Win rate (%)
- Average R:R ratio
- Total profit/loss
- Max drawdown
- Sharpe ratio
- Profit factor

---

## 📁 Project Structure

```
Kam_Algo/
│
├── config/
│   ├── settings.py              # Trading parameters
│   └── secrets.env              # API keys (DO NOT COMMIT TO GIT)
│
├── src/
│   ├── data/
│   │   └── ib_data_feed.py      # Interactive Brokers connection
│   │
│   ├── strategy/
│   │   ├── confirmation1_sweep.py       # Liquidity sweep detection
│   │   ├── confirmation2_htf_fvg.py     # HTF FVG delivery
│   │   ├── confirmation3_ifvg.py        # iFVG inversion
│   │   ├── confirmation4_cisd.py        # CISD structure break
│   │   ├── confirmation5_momentum.py    # Momentum filter (optional)
│   │   └── signal_generator.py          # Combines all confirmations
│   │
│   ├── risk/
│   │   └── position_sizing.py   # Risk management & position sizing
│   │
│   ├── alerts/
│   │   ├── discord_bot.py       # Discord notifications
│   │   └── telegram_bot.py      # Telegram notifications
│   │
│   └── filters/
│       └── time_filter.py       # Trading session filters
│
├── data/
│   └── ib_data_feed.py          # Data download scripts
│
├── logs/
│   └── system.log               # System logs (auto-generated)
│
├── results/
│   └── backtest_results.csv     # Backtest results (auto-generated)
│
├── screenshots/                 # Chart screenshots (auto-generated)
│
├── main.py                      # ← LIVE TRADING - RUN THIS
├── backtest_main.py             # ← BACKTESTING - RUN THIS
├── download_ib_data.py          # Historical data downloader
├── test_alert.py                # Test Discord/Telegram alerts
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore file
└── README.md                    # ← YOU ARE HERE
```

---

## 🔧 Troubleshooting

### Error: "Failed to connect to IB"

**Causes:**
- TWS is not running
- TWS is not logged in
- API is not enabled
- Wrong port number

**Solutions:**
1. Launch TWS and log in
2. File → Global Configuration → API → Settings
3. Enable "ActiveX and Socket Clients"
4. Port: `7497` (paper) or `7496` (live)
5. Restart TWS
6. Run `python main.py` again

---

### Error: "Discord webhook failed"

**Causes:**
- Invalid webhook URL
- Webhook deleted
- Network issues

**Solutions:**
1. Verify webhook URL in `config/secrets.env`
2. Test webhook manually:
   ```bash
   python test_alert.py
   ```
3. Create new webhook if needed
4. Check internet connection

---

### Error: "No historical data"

**Causes:**
- TWS not fully logged in
- Market data subscription missing
- Symbol not available

**Solutions:**
1. Wait 30 seconds after TWS login
2. Check market data subscriptions in TWS
3. Verify symbol is correct (`MNQ`, `MES`, etc.)
4. Try downloading data manually:
   ```bash
   python download_ib_data.py
   ```

---

### Warning: "Read-only mode"

**This is OK** for our system (we only read data, not place orders).

**To remove warning:**
1. TWS → API Settings
2. Uncheck "Read-Only API"
3. Restart TWS

---

### Error: "Module not found"

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Activate venv
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### System not detecting signals

**Possible causes:**
1. **Market conditions**: No valid setups during session
2. **Parameters too strict**: Adjust thresholds in `config/settings.py`
3. **Time filter**: Check trading hours match your timezone

**Debug steps:**
1. Check logs: `logs/system.log`
2. Run backtest to verify strategy logic
3. Lower confirmation thresholds temporarily for testing
4. Verify real-time data is flowing (check TWS)

---

## 📈 Trading Workflow

### Daily Routine

**Before Market Open (9:00 AM EST):**
1. Start TWS and log in to paper account
2. Activate virtual environment: `venv\Scripts\activate`
3. Run system: `python main.py`
4. Verify connection: Check for "✅ Connected to IB" message
5. Open Discord on phone for alerts

**During Trading Session (9:30-11:00 AM EST):**
1. System monitors automatically
2. When alert received:
   - **Read alert** (15 seconds)
   - **Verify on TradingView** (30 seconds)
   - **Check all 4 confirmations** visually
   - **Execute in prop firm platform** (1 minute)
   - **Log trade** in spreadsheet
3. Wait for next signal

**After Trading Session (11:00 AM EST):**
1. System stops automatically
2. Review logs: `logs/system.log`
3. Update trade journal
4. Calculate daily P&L
5. Plan for next session

### Weekly Routine

**Sunday Evening:**
- Review previous week's performance
- Adjust parameters if needed (cautiously)
- Plan week ahead

**Friday Evening:**
- Calculate weekly P&L
- Review win rate and R:R
- Document lessons learned
- Prepare for next week

---

## ⚠️ Important Notes

### Trading Rules (DO NOT BREAK):
1. ✅ **Never override the 4 confirmations rule** - If all 4 don't align, NO TRADE
2. ✅ **Never increase risk after losses** - Stick to 0.5% per trade
3. ✅ **Never trade outside 9:30-11:00 AM EST** - Highest volume period only
4. ✅ **Always log every trade** - Track performance religiously
5. ✅ **Paper trade first** - Minimum 2 weeks before going live
6. ✅ **Never revenge trade** - Take breaks after losses
7. ✅ **Respect max daily loss** - Stop at -3% daily drawdown

### Risk Management:
- **Position sizing**: Automatically calculated based on stop distance
- **Max risk per trade**: 0.5% of account (adjustable)
- **Max daily loss**: 3% of account
- **Max drawdown**: 6% before re-evaluation

### Prop Firm Compliance:
- ✅ **Semi-automated = Legal** - Algo detects, human executes
- ✅ **No auto-trading** - All orders placed manually
- ✅ **Full control** - You decide every trade
- ✅ **Audit trail** - All signals logged

### Data & Privacy:
- **API keys**: Never commit `secrets.env` to Git
- **Logs**: Contain sensitive data, keep private
- **Backtest results**: For personal use only

---

## 🎯 Next Steps

### Week 1: Paper Trading
- Run system daily 9:30-11:00 AM EST
- Execute ALL signals in paper account
- Log every trade with screenshots
- Track performance metrics

### Week 2: Optimization
- Review what worked/didn't work
- Adjust parameters if needed (cautiously)
- Fine-tune risk sizing
- Build confidence

### Week 3: Go Live (Small)
- Switch to real prop firm account
- Start with smallest challenge ($25K-$50K)
- Execute same as paper trading
- Document everything

### Month 2+: Scale
- Pass challenges consistently
- Get funded accounts
- Add multiple accounts
- Grow to $400K+ total capital

---

## 📞 Support & Contact

**Issues or Questions?**
- Check logs: `logs/system.log`
- Review this README thoroughly
- Test components individually (`test_alert.py`, etc.)

**Contact:**
- Email: rimerizha@gmail.com
- Discord: @rhimcapital

---

## 🎬 Your Trading Journey Starts Now

**Document Everything:**
- Daily trading videos
- Twitter/social media updates
- Trade screenshots
- Lessons learned
- Performance metrics

**Stay Disciplined:**
- Follow the rules
- Trust the process
- Manage risk religiously
- Never stop learning

**Let's build wealth together.** 🚀

---

## 📝 License & Disclaimer

**Disclaimer:** Trading futures involves substantial risk of loss. This software is provided for educational purposes only. Past performance does not guarantee future results. Always paper trade before risking real capital. The creators are not responsible for any financial losses incurred using this system.

**License:** For personal use only. Do not distribute or sell without permission.

---

**Version:** 1.0.0  
**Last Updated:** January 22, 2026  
