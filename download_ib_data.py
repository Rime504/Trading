"""
Download historical data from Interactive Brokers
"""

import asyncio
import sys

# FIX: eventkit (used by ib_insync) requires an event loop at import time
# Create loop before importing ib_insync
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from ib_insync import IB, Future, util
import pandas as pd
from datetime import datetime, timedelta


async def download_historical_data():
    """Download historical data from IB"""
    
    # Connect to IB
    ib = IB()
    try:
        # Using connectAsync should be fine within the loop
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        print("✅ Connected to IB")
        
        # Search for MNQ contracts
        print("🔍 Searching for MNQ contracts...")
        contract_pattern = Future('MNQ', includeExpired=False)
        details = await ib.reqContractDetailsAsync(contract_pattern)
        
        if not details:
            print("❌ No MNQ contracts found")
            # Try CME
            contract_pattern = Future('MNQ', exchange='CME', includeExpired=False)
            details = await ib.reqContractDetailsAsync(contract_pattern)
            
        if not details:
             print("❌ No MNQ contracts found on GLOBEX or CME")
             return

        # Find March 2025 contract
        target_contract = None
        for d in details:
            c = d.contract
            # Check for main contract matching 202503
            if c.lastTradeDateOrContractMonth.startswith('202503'):
                target_contract = c
                break
        
        # If not found, look for next expiry
        if not target_contract:
            # Sort by date
            sorted_details = sorted(details, key=lambda x: x.contract.lastTradeDateOrContractMonth)
            current_date = datetime.now().strftime("%Y%m%d")
            for d in sorted_details:
                if d.contract.lastTradeDateOrContractMonth > current_date:
                    target_contract = d.contract
                    break
        
        if not target_contract:
            print("❌ Could not find any valid future contract")
            return
            
        contract = target_contract
        print(f"✅ Selected contract: {contract.localSymbol} ({contract.lastTradeDateOrContractMonth})")

        # Qualify it (refresh ID and details)
        await ib.qualifyContractsAsync(contract)
        
        # Download historical data
        print("\n📊 Downloading historical data...")
        
        # Get 30 days of 5-minute bars
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr='30 D',
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=False  # Include extended hours
        )
        
        if not bars:
            print("❌ No data downloaded")
            return

        print(f"✅ Downloaded {len(bars)} bars")
        
        # Convert to DataFrame
        df = util.df(bars)
        
        # Save to CSV
        filename = 'data/MNQ_historical_30days.csv'
        df.to_csv(filename)
        print(f"✅ Saved to {filename}")
        
        # Show sample
        print("\n📊 Sample data:")
        print(df.head())
        print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Disconnect
        ib.disconnect()
        print("\n✅ Done!")


if __name__ == "__main__":
    # Use the existing loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_historical_data())