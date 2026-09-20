import asyncio
from bleak import BleakScanner, BleakClient

async def main():
    print("Scanning for GATT--DEMO...")
    device = await BleakScanner.find_device_by_name("GATT--DEMO", timeout=10)
    if not device:
        print("Device not found. Is it powered on and not connected elsewhere?")
        return

    print(f"Found {device.name} @ {device.address}")

    async with BleakClient(device) as client:
        print("Connected!")
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Char: {char.uuid} | {char.properties}")

        # Try the known red command for MR Star / GATT--DEMO
        # (Write to the correct characteristic—adjust UUID if needed)
        # Example UUIDs from reverse engineering: often 0000fff3-0000-1000-8000-00805f9b34fb
        # Use the UUID you used before.
        # await client.write_gatt_char("YOUR_CHAR_UUID", bytes.fromhex("bc0406000003e8000055"))
        # print("Red command sent.")

asyncio.run(main())