import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"
CHAR = "0000fff3-0000-1000-8000-00805f9b34fb"

async def main():
    print("Connecting...")
    async with BleakClient(ADDRESS) as client:
        print("Connected! WATCH THE STRIP.")
        print("-- OFF --")
        await client.write_gatt_char(CHAR, bytes.fromhex("cc2433"))
        await asyncio.sleep(2)
        print("-- ON --")
        await client.write_gatt_char(CHAR, bytes.fromhex("cc2333"))
        await asyncio.sleep(2)
        print("-- RED --")
        await client.write_gatt_char(CHAR, bytes.fromhex("56ff000000f0aa"))
        await asyncio.sleep(2)
        print("-- GREEN --")
        await client.write_gatt_char(CHAR, bytes.fromhex("5600ff0000f0aa"))
        await asyncio.sleep(2)
        print("-- BLUE --")
        await client.write_gatt_char(CHAR, bytes.fromhex("560000ff00f0aa"))
        await asyncio.sleep(2)
        print("Done.")

asyncio.run(main())