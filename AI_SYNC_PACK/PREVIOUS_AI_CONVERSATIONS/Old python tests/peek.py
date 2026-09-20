import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"

async def main():
    print(f"Connecting to {ADDRESS} ...")
    async with BleakClient(ADDRESS) as client:
        print("Connected!")
        print("\nList of characteristics:")
        for service in client.services:
            for char in service.characteristics:
                print(f"   {char.uuid}  ->  {char.properties}")
    print("Disconnected. Done.")

asyncio.run(main())