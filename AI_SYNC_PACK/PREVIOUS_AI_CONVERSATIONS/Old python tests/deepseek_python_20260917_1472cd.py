import asyncio
from bleak import BleakClient

ADDRESS = "41:42:59:F1:C8:68"   # ONE strip only, for clean testing

# ---- Exact bytes captured from your phone's btsnoop ----
SETUP = [
    "BC0F010155",
    "BC11010455",
]

DATA = [
    "BC0406000003E8000055",
    "BC0406013E0032000055",
    "BC04060131002B000055",
    "BC040600E200A8000055",
]

async def try_sequence(client, char_uuid, with_response, label):
    print(f"\n--- {label}  (response={with_response}) ---")
    try:
        for h in SETUP:
            for _ in range(3):
                await client.write_gatt_char(char_uuid, bytes.fromhex(h), response=with_response)
                await asyncio.sleep(0.005)
            await asyncio.sleep(0.03)

        await asyncio.sleep(0.1)

        for d in DATA:
            for _ in range(3):
                await client.write_gatt_char(char_uuid, bytes.fromhex(d), response=with_response)
                await asyncio.sleep(0.005)
            await asyncio.sleep(0.06)
            print(f"   sent {d}")
        print("   sequence sent OK")
    except Exception as e:
        print(f"   ERROR: {e}")

async def main():
    print("MAKE SURE PHONE BLUETOOTH IS OFF AND MR STAR APP IS CLOSED")
    input("Press Enter when ready...")

    async with BleakClient(ADDRESS, timeout=15.0) as client:
        print("Connected.")

        # locate the real UUIDs / handles
        fff3 = ff15 = None
        for svc in client.services:
            for ch in svc.characteristics:
                if "fff3" in ch.uuid.lower():
                    fff3 = ch.uuid
                if "ff15" in ch.uuid.lower():
                    ff15 = ch.uuid
        print(f"FFF3 = {fff3}")
        print(f"FF15 = {ff15}")

        # --- test matrix ---
        if fff3:
            await try_sequence(client, fff3, False, "FFF3 / without response")
            await asyncio.sleep(2)
            await try_sequence(client, fff3, True,  "FFF3 / with response")
            await asyncio.sleep(2)

        if ff15:
            await try_sequence(client, ff15, False, "FF15 / without response")
            await asyncio.sleep(2)

        print("\n=== DONE. Watch the strip the whole time. ===")

asyncio.run(main())