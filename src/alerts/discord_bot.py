"""
Discord Alert System - FIXED VERSION
Sends formatted alerts when signals are generated
"""

import logging
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv('config/secrets.env')

logger = logging.getLogger(__name__)


class DiscordAlerter:
    """Send trading signals to Discord"""
    
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not self.webhook_url:
            logger.error("DISCORD_WEBHOOK_URL not found in config/secrets.env")
        else:
            logger.info("✅ Discord alerter initialized")
    
    def send_signal_alert(self, signal: Dict, position_size: Dict, 
                         symbol: str = 'MNQ') -> bool:
        """Send signal alert with all details"""
        if not self.webhook_url:
            logger.error("Cannot send alert - no webhook URL")
            return False
        
        try:
            # Format time
            signal_time = signal['time']
            if hasattr(signal_time, 'strftime'):
                time_str = signal_time.strftime('%H:%M:%S EST')
            else:
                time_str = str(signal_time)
            
            # Build the message content
            direction_emoji = "🔴" if signal['direction'] == 'SHORT' else "🟢"
            
            # Create embed
            embed = {
                "title": f"{direction_emoji} CONFIRMATION MODEL SIGNAL - {symbol} {signal['direction']}",
                "color": 16711680 if signal['direction'] == 'SHORT' else 65280,  # Red or Green
                "fields": [
                    {
                        "name": "📊 Instrument",
                        "value": symbol,
                        "inline": True
                    },
                    {
                        "name": "⏰ Time",
                        "value": time_str,
                        "inline": True
                    },
                    {
                        "name": "📍 Direction",
                        "value": f"**{signal['direction']}**",
                        "inline": True
                    },
                    {
                        "name": "✅ Confirmations",
                        "value": (
                            f"✅ **1. Liquidity Sweep**\n"
                            f"   Swept {signal['confirmations']['sweep']['type']} at {signal['confirmations']['sweep']['swing_level']:.2f}\n\n"
                            f"✅ **2. HTF FVG Delivery**\n"
                            f"   {signal['confirmations']['htf_fvg']['fvg']['type'].upper()} FVG: "
                            f"{signal['confirmations']['htf_fvg']['fvg']['bottom']:.2f}-{signal['confirmations']['htf_fvg']['fvg']['top']:.2f}\n\n"
                            f"✅ **3. iFVG Inversion**\n"
                            f"   {signal['confirmations']['ifvg']['type']}\n\n"
                            f"✅ **4. CISD**\n"
                            f"   Structure broken at {signal['confirmations']['cisd']['cisd_level']:.2f}"
                        ),
                        "inline": False
                    },
                    {
                        "name": "📊 Trade Setup",
                        "value": (
                            f"📈 **ENTRY**: {signal['entry']:.2f} (market)\n"
                            f"🛑 **STOP**: {signal['stop_loss']:.2f} ({signal['risk']:.2f} pts)\n"
                            f"🎯 **TARGET**: {signal['target']:.2f} ({signal['reward']:.2f} pts)\n"
                            f"💰 **R:R**: 1:{signal['risk_reward_ratio']:.1f}"
                        ),
                        "inline": False
                    },
                    {
                        "name": "💰 Position Details",
                        "value": (
                            f"📊 **SIZE**: {position_size['contracts']} contract(s)\n"
                            f"💵 **RISK**: ${position_size['total_risk_dollars']:.2f} "
                            f"({position_size['risk_percentage']:.2f}%)\n"
                            f"💰 **POTENTIAL**: ${position_size['contracts'] * signal['reward'] * position_size['tick_value']:.2f}"
                        ),
                        "inline": False
                    },
                    {
                        "name": "⏳ Validity",
                        "value": "**Valid for 5 minutes** - Execute quickly!",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Confirmation Model Algo | @rhimcapital"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send webhook
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 204]:
                logger.info("✅ Discord alert sent successfully")
                return True
            else:
                logger.error(f"❌ Discord alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False
    
    def send_system_message(self, message: str) -> bool:
        """Send simple text message"""
        if not self.webhook_url:
            return False
        
        try:
            payload = {
                "content": message
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error sending system message: {e}")
            return False
    
    def send_daily_summary(self, trades: list, pnl: float) -> bool:
        """Send end-of-day summary"""
        if not self.webhook_url:
            return False
        
        try:
            embed = {
                "title": "📊 Daily Trading Summary",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "📈 Signals Today",
                        "value": f"{len(trades)} signals generated",
                        "inline": True
                    },
                    {
                        "name": "💰 P&L",
                        "value": f"${pnl:.2f}",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False