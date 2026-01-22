"""
Test Signal Alert - Simulates what sister will see
"""

from src.alerts.discord_bot import DiscordAlerter
from datetime import datetime

# Create test signal (fake data, just for testing)
test_signal = {
    'time': datetime.now(),
    'direction': 'SHORT',
    'entry': 16515.00,
    'stop_loss': 16527.00,
    'target': 16491.00,
    'risk': 12.0,
    'reward': 24.0,
    'risk_reward_ratio': 2.0,
    'confirmations': {
        'sweep': {
            'type': 'buyside_sweep',
            'swing_level': 16525.00
        },
        'htf_fvg': {
            'fvg': {
                'type': 'bearish',
                'bottom': 16518.00,
                'top': 16522.00
            }
        },
        'ifvg': {
            'type': 'bullish_fvg_disrespected'
        },
        'cisd': {
            'cisd_level': 16517.00
        }
    }
}

# Create test position size
test_position = {
    'contracts': 3,
    'total_risk_dollars': 240.00,
    'risk_percentage': 0.48,
    'tick_value': 2.0
}

# Send test alert
alerter = DiscordAlerter()
print("📤 Sending test alert...")
success = alerter.send_signal_alert(test_signal, test_position, 'MNQ')

if success:
    print("✅ TEST ALERT SENT!")
    print("👉 Check Discord - your sister should see a full signal alert")
else:
    print("❌ Failed to send alert")