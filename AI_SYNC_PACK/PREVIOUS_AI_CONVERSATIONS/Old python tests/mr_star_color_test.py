import asyncio
from bleak import BleakClient

# Your strip's MAC address
STRIP_MAC = "41:42:43:E7:8B:F6" 
# The correct UUID for writing commands
CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

# The corrected color commands using register 01
COMMANDS = [
    ("OFF (Reset)", "bc01010055"),
    ("ON (White Default)", "bc01010155"),
    ("RED (Corrected)", "bc0401ff00000055"),
    ("GREEN", "bc040100ff000055"),
    ("BLUE", "bc04010000ff0055"),
    ("OFF (Final Reset)", "bc01010055"),
]

async def main():
    print(f"Connecting to {STRIP_MAC}...")
    client = BleakClient(STRIP_MAC)
    
    try:
        await client.connect()
        print("Connected!\n")
        await asyncio.sleep(1)
        
        for name, hex_str in COMMANDS:
            if not client.is_connected:
                print("Disconnected! Reconnecting...")
                await client.connect()
                await asyncio.sleep(1)
            
            print(f"Sending: {name} ({hex_str})")
            data = bytes.fromhex(hex_str)
            await client.write_gatt_char(CHAR_UUID, data, response=False)
            
            # Wait 2 seconds for you to watch the strip
            await asyncio.sleep(2)
            print("---")
        
        print("\nTest complete! Did it turn Red, then Green, then Blue?")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())