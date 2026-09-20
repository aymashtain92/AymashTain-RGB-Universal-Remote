import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for 10 seconds... make sure strips are ON")
    devices = await BleakScanner.discover(timeout=10)
    print("\nFound these Bluetooth devices:")
    print("-" * 45)
    for d in devices:
        name = d.name if d.name else "(no name)"
        print(f"{name:30} | {d.address}")
    print("-" * 45)
    print("Done. Take a photo or screenshot of this list.")

asyncio.run(main())