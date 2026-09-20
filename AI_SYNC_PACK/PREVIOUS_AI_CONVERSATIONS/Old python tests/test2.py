import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"
FFF3 = "0000fff3-0000-1000-8000-00805f9b34fb"
FF15 = "0000ff15-0000-1000-8000-00805f9b34fb"

async def attempt(client, char, hexstr, label, resp):
    print(f"--> {label}")
    try:
        await client.write_gatt_char(char, bytes.fromhex(hexstr), response=resp)
        print("    sent (no error)")
    except Exception as e:
        print(f"    ERROR: {e}")
    await asyncio.sleep(3)

async def main():
    async with BleakClient(ADDRESS) as client:
        print("Connected. WATCH THE STRIP the whole time.")
        print()
        await attempt(client, FF15, "cc2333", "Try 1: FF15, ON", False)
        await attempt(client, FF15, "cc2433", "Try 2: FF15, OFF", False)
        await attempt(client, FFF3, "cc2333", "Try 3: FFF3, ON, different write style", True)
        await attempt(client, FFF3, "cc2433", "Try 4: FFF3, OFF, different write style", True)
        await attempt(client, FF15, "cc2333", "Try 5: FF15, ON, different write style", True)
        await attempt(client, FF15, "cc2433", "Try 6: FF15, OFF, different write style", True)
        print()
        print("All done.")

asyncio.run(main())