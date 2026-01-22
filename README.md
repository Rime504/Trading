Confirmation Model Algo Trading System
Your journey from $0 to $1M in 2026

🎯 What This Is
A semi-automated trading system that detects high-probability setups using The Confirmation Model (4 confirmations) and sends instant alerts to Discord/Telegram for manual execution.

Why Semi-Automated?

Prop firms don't allow full automation during challenges
Your sister executes manually (legal & compliant)
Algo does the heavy lifting (finds setups 24/7)
🚀 Quick Start
1. Prerequisites
# Verify Python installation
python --version  # Should be 3.10+

# Verify you're in project folder
cd C:\Users\hp\OneDrive\CR_CAPITAL\Kam_Algo

# Activate virtual environment
venv\Scripts\activate
2. Configure Settings
Edit config/secrets.env:

# Interactive Brokers
IB_HOST=127.0.0.1
IB_PORT=7497  # 7497 for paper, 7496 for live
IB_CLIENT_ID=1

# Discord Webhook
DISCORD_WEBHOOK_URL=YOUR_ACTUAL_WEBHOOK_HERE

# Account Settings
ACCOUNT_SIZE=50000
RISK_PER_TRADE=0.005
3. Start Interactive Brokers TWS
Open TWS (Trader Workstation)
Log in to paper trading account (red "DEMO SYSTEM" banner)
File → Global Configuration → API → Settings
Enable API, port 7497
Click OK
4. Run The System
python main.py
You should see:

[2026-01-03 09:25:00] System starting...
[2026-01-03 09:25:01] ✅ Connected to IB at 127.0.0.1:7497
[2026-01-03 09:25:02] ✅ Subscribed to MNQ real-time data
[2026-01-03 09:25:05] ✅ Loaded 1440 historical bars
[2026-01-03 09:25:05] 👀 Monitoring loop started
[2026-01-03 09:25:06] ⏰ Market opens in 4 minutes
📊 How It Works
The 4 Confirmations
Every signal requires ALL FOUR to align:

✅ Liquidity Sweep: Price takes out swing high/low and reverses
✅ HTF FVG Delivery: 15m/1h FVG respected (rejection)
✅ iFVG Inversion: 1-5m FVG disrespected (closes through)
✅ CISD: Structure breaks (closes through pre-sweep candle series)
When Signal Appears
Discord alert arrives on your phone:

All 4 confirmations details
Entry price
Stop loss
Target
Position size (contracts)
Risk/reward ratio
Chart screenshot
Your sister:

Sees alert (15 seconds)
Verifies on TradingView (30 seconds)
Executes in prop firm platform (1 minute)
Logs trade
⚙️ Configuration
Change Instruments
Edit config/settings.py:

PRIMARY_INSTRUMENT = 'MNQ'  # or 'ES', 'NQ'
Change Risk
Edit config/secrets.env:

RISK_PER_TRADE=0.005  # 0.5% (conservative)
# or
RISK_PER_TRADE=0.01   # 1.0% (aggressive)
Change Trading Hours
Edit config/settings.py:

TRADING_START_TIME = "09:30"
TRADING_END_TIME = "11:00"
📁 Project Structure
Kam_Algo/
├── config/
│   ├── settings.py          # All parameters
│   └── secrets.env          # API keys (DO NOT COMMIT)
├── src/
│   ├── data/
│   │   └── ib_data_feed.py  # IB connection
│   ├── strategy/
│   │   ├── confirmation1_sweep.py
│   │   ├── confirmation2_htf_fvg.py
│   │   ├── confirmation3_ifvg.py
│   │   ├── confirmation4_cisd.py
│   │   └── signal_generator.py
│   ├── risk/
│   │   └── position_sizing.py
│   └── alerts/
│       └── discord_bot.py
├── logs/                    # System logs
├── results/                 # Trade results
├── screenshots/             # Chart screenshots
├── main.py                  # ← RUN THIS
└── README.md               # ← YOU ARE HERE
🔧 Troubleshooting
"Failed to connect to IB"
Make sure TWS is open and logged in
Check port is 7497 (paper) or 7496 (live)
In TWS: File → Global Configuration → API → Enable API
"Discord webhook failed"
Verify webhook URL in config/secrets.env
Test: Send test message in Discord channel
"No historical data"
TWS needs to be logged in
Wait 30 seconds after TWS login
Check you have market data subscription
"Read-only mode" warnings
This is OK for our system (we only read data)
To fix: TWS → API Settings → Uncheck "Read-Only API"
📈 Next Steps
Week 1: Paper Trading
Run system every day 9:30-11:00 AM
Sister executes ALL signals in paper account
Log every trade
Track performance
Week 2: Optimize
Review what worked
Adjust parameters if needed
Fine-tune risk sizing
Week 3: Go Live
Switch to real prop firm account
Start with smallest challenge ($25K-$50K)
Document everything
Month 2+: Scale
Pass challenges
Get funded
Multiple accounts
Grow to $400K+ total
📞 Support
Issues?

Check logs: logs/system.log
Discord: @rhimcapital
Email: kameliakaut@gmail.com
⚠️ Important Notes
Never override the 4 confirmations rule
Never increase risk after losses
Never trade outside 9:30-11:00 AM EST
Always log every trade
Paper trade first
🎬 Your $0→$1M Journey Starts Now
Document everything:

Daily videos
Twitter updates
Trade screenshots
Lessons learned
Let's go. 🚀
