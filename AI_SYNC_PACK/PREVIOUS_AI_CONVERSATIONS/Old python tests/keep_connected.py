import asyncio
from bleak import BleakClient

# Your verified hardware MAC address
ADDRESS = "41:42:59:F1:C8:68"

async def main():
    print(f"Connecting to {ADDRESS} to establish Windows system link...")
    
    try:
        # We initialize the client
        async with BleakClient(ADDRESS) as client:
            if client.is_connected:
                print("\n==================================================")
                print(" SUCCESS: Device is now linked to your PC!")
                print(" Check your Windows Bluetooth Settings right now.")
                print(" It will show as 'Connected'.")
                print("==================================================")
                print("\n Keeping connection alive... Press CTRL + C to disconnect.")
                
                # This infinite loop forces the connection to stay open
                while True:
                    # Send a tiny "heartbeat" read request every 10 seconds 
                    # to prevent Windows from timing out the connection
                    await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                    await asyncio.sleep(10)
                    
    except asyncio.CancelledError:
        print("\nDisconnecting cleanly from device...")
    except Exception as e:
        print(f"\nConnection lost or failed: {e}")

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nScript stopped by user. Windows connection closed.")
