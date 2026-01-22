import asyncio
import sys

# Ensure an event loop exists before importing libraries that might require it at module level
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

try:
    from ib_insync import IB, util
    print(f"✅ ib_insync version: {IB.__module__} (imported successfully)")
except Exception as e:
    print(f"❌ Failed to import ib_insync: {e}")
    sys.exit(1)

async def check_connection():
    ib = IB()
    print("🤖 IB Instance created.")
    
    print("📡 Attempting to connect to IB Gateway/TWS (127.0.0.1:7497)...")
    try:
        # Using a short timeout to not hang if TWS is closed
        await asyncio.wait_for(ib.connectAsync('127.0.0.1', 7497, clientId=1), timeout=5.0)
        print("✅ Success! Connected to IB.")
        ib.disconnect()
        print("🔌 Disconnected.")
    except asyncio.TimeoutError:
        print("⚠️  Connection timed out. Is TWS/Gateway running and configured for API port 7497?")
    except ConnectionRefusedError:
        print("❌ Connection refused. TWS/Gateway is likely not running or port 7497 is blocked.")
    except Exception as e:
        print(f"⚠️  Connection error (expected if TWS is closed): {e}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(check_connection())
    except KeyboardInterrupt:
        print("\nExiting...")
