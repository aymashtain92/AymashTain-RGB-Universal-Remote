import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"
HANDLE_ID = 13  # Your verified physical handle

async def brute_force_lenze_protocol(client):
    print("\n" + "="*60)
    print(" 🚀 STARTING LOGICAL PROTOCOL CYCLER ON HANDLE 13")
    print(" Make sure loud music is playing near the USB microphone box!")
    print(" Watch the ceiling—press CTRL + C immediately if the strip reacts.")
    print("="*60 + "\n")

    # Range 1: Sweep through the 3rd byte (Command category registers)
    # Form: 7e 00 XX 01 04 00 00 00 ef
    print("[Phase 1] Testing Command Category Registers...")
    for cmd_byte in range(0x01, 0x10):  # Cycles from 01 to 0f
        hex_str = f"7e00{cmd_byte:02x}0104000000ef"
        print(f"Sending Category Test: {hex_str}")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"   Skipped: {e}")
        await asyncio.sleep(0.4)

    # Range 2: Sweep through the 5th byte (Mode/Pattern Index registers)
    # Form: 7e 00 04 01 XX 00 00 00 ef
    print("\n[Phase 2] Testing Internal Pattern Index Registers...")
    for pattern_byte in range(0x00, 0x20):  # Cycles 32 variations from 00 to 1f
        hex_str = f"7e000401{pattern_byte:02x}000000ef"
        print(f"Sending Pattern Test: {hex_str}")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"   Skipped: {e}")
        await asyncio.sleep(0.4)

    # Range 3: Short 4-Byte Packet Type Matrix (Used by smaller dynamic chips)
    # Form: 7e XX YY ef
    print("\n[Phase 3] Testing Compressed 4-Byte Handshake Matrix...")
    for b2 in [0x04, 0x05, 0x07]:
        for b3 in range(0x01, 0x10):
            hex_str = f"7e{b2:02x}{b3:02x}ef"
            print(f"Sending Compressed Handshake: {hex_str}")
            try:
                await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
            except Exception as e:
                print(f"   Skipped: {e}")
            await asyncio.sleep(0.4)

    print("\n" + "="*60)
    print(" Sequence sweep completed. If nothing happened, the firmware requires")
    print(" a highly custom security initialization payload via Handle 13.")
    print("="*60)

async def main():
    print(f"Connecting to hardware interface {ADDRESS}...")
    try:
        async with BleakClient(ADDRESS, timeout=15.0) as client:
            if client.is_connected:
                await brute_force_lenze_protocol(client)
            else:
                print("Could not attach to the device endpoint.")
    except Exception as e:
        print(f"Session error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSweep stopped by user.")
