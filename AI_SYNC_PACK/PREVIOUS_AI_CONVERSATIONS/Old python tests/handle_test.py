import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"
HANDLE_ID = 19  # Swapping to your alternative write port

async def sweep_handle_19(client):
    print("\n" + "="*60)
    print(" 🚀 TARGETING ALTERNATIVE HANDLE 19 PROTOCOL MATRIX")
    print(" Make sure music or loud clapping sound is active near the box!")
    print(" Keep your eyes on the strips — hit CTRL + C if they jump.")
    print("=" * 60 + "\n")

    # Group 1: The '56' command variants targeting Handle 19 music modes
    # Form: 56 00 00 00 XX f0 aa
    print("[Group 1] Testing 56-Prefix Sound Mapping...")
    # Common sound activation indexes: 01-06, 81-86, or mode selectors
    test_bytes = [0x01, 0x02, 0x03, 0x04, 0x05, 0x81, 0x82, 0x83, 0x84, 0x14, 0x15]
    for b in test_bytes:
        hex_str = f"56000000{b:02x}f0aa"
        print(f"Sending to H19: {hex_str}")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"   Failed packet: {e}")
        await asyncio.sleep(0.4)

    # Group 2: The '7e' 9-byte structure variants targeting Handle 19
    # Form: 7e 00 04 01 XX 00 00 00 ef
    print("\n[Group 2] Testing 7e-Prefix Structural Patterns...")
    for pattern_idx in range(0x01, 0x0a):  # Standard built-in mode index sweep
        hex_str = f"7e000401{pattern_idx:02x}000000ef"
        print(f"Sending to H19: {hex_str}")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"   Failed packet: {e}")
        await asyncio.sleep(0.4)

    # Group 3: Alternative custom structure headers (7e 04 04...)
    print("\n[Group 3] Testing Multi-Mode Flow Structures...")
    alt_structures = [
        "7e0404f00001ff00ef",
        "7e0404000000ff00ef",
        "7e05039c03ffff00ef",
        "7e05039803ffff00ef"
    ]
    for hex_str in alt_structures:
        print(f"Sending to H19: {hex_str}")
        try:
            await client.write_gatt_char(HANDLE_ID, bytes.fromhex(hex_str), response=False)
        except Exception as e:
            print(f"   Failed packet: {e}")
        await asyncio.sleep(0.4)

    print("\n" + "="*60)
    print(" Sweep complete on alternative handle 19.")
    print("="*60)

async def main():
    print(f"Connecting to hardware interface {ADDRESS}...")
    try:
        async with BleakClient(ADDRESS, timeout=15.0) as client:
            if client.is_connected:
                await sweep_handle_19(client)
            else:
                print("Could not attach to the device endpoint.")
    except Exception as e:
        print(f"Session error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSweep stopped by user.")
