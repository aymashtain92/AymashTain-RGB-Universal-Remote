import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for 30 seconds... keep strips ON and close to PC")
    print("=" * 50)
    
    devices = await BleakScanner.discover(timeout=30)
    
    print("\nAll found devices:")
    print("-" * 50)
    for d in devices:
        name = d.name if d.name else "UNKNOWN"
        rssi = d.rssi if hasattr(d, 'rssi') and d.rssi else "?"
        print(f"NAME: {name:25} | ADDR: {d.address} | SIGNAL: {rssi}")
    print("-" * 50)
    print(f"Total devices found: {len(devices)}")
    print("Done.")

asyncio.run(main())