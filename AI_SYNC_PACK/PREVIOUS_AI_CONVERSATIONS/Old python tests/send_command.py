import asyncio
from bleak import BleakClient

# The address of your strip
ADDRESS = "41:42:59:F1:C8:68"
# Your verified physical characteristic handle for sending commands
HANDLE_ID = 13

async def main():
    # We use a quick standalone connection to inject the pattern command
    async with BleakClient(ADDRESS) as client:
        # This hex code tells the MR Star chip to switch to its internal Scroll pattern
        scroll_hex = "7e00040104000000ef"
        
        print(f"Injecting Scroll Pattern command to Handle {HANDLE_ID}...")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(scroll_hex), response=False)
            print("🚀 Command successfully injected! Check your LED strips.")
        except Exception as e:
            print(f"Injection failed: {e}")

asyncio.run(main())
