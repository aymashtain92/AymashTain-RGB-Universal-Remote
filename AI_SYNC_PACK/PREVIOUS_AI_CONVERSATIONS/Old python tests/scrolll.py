import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"
CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

async def test_modes(client):
    # These are the standard hex commands for built-in music/dynamic modes
    # The 5th byte (01, 02, 03...) tells the chip which specific pattern to load
    music_modes = {
        "Mode 1": "7e00040101000000ef",
        "Mode 2": "7e00040102000000ef",
        "Mode 3": "7e00040103000000ef",
        "Mode 4": "7e00040104000000ef",
        "Mode 5": "7e00040105000000ef",
        "Mode 6": "7e00040106000000ef",
    }

    for name, hex_str in music_modes.items():
        print(f"Testing {name}... sending {hex_str}")
        try:
            await client.write_gatt_char(CHAR_UUID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"Error: {e}")
        
        print("Make some noise! Check if the strips are scrolling/dancing...")
        await asyncio.sleep(5)  # Gives you 5 seconds to look at the ceiling

async def main():
    print(f"Connecting to {ADDRESS}...")
    async with BleakClient(ADDRESS) as client:
        print("Connected! Starting loop...")
        await test_modes(client)
    print("Done testing.")

asyncio.run(main())
