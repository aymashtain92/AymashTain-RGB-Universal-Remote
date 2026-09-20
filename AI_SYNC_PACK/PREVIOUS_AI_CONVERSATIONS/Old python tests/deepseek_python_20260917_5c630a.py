import asyncio
from bleak import BleakClient

# ---- test on ONE strip first so we can be sure ----
ADDRESS = "41:42:59:F1:C8:68"

# ---- Exact bytes from your btsnoop capture ----
SETUP = [
    "BC0F010155",
    "BC11010455",
]

DATA = [
    "BC0406000003E8000055",
    "BC0406013E0032000055",
    "BC04060131002B000055",
    "BC040600E200A8000055",
    "BC040600E400B8000055",
    "BC040600E60091000055",
    "BC040600E90046000055",
    "BC040600F00027000055",
    "BC040600F00023000055",
    "BC040600F00023000055",
    "BC040600FF003E000055",
    "BC040601050081000055",
    "BC0406011B00EB000055",
    "BC0406013D01A3000055",
    "BC0406014D0230000055",
    "BC04060161026F000055",
    "BC0406001B02FC000055",
    "BC0406002C0372000055",
    "BC0406003E02E1000055",
    "BC0406005A0215000055",
    "BC0406008701BF000055",
    "BC040600B00215000055",
    "BC040600C90296000055",
    "BC040600DF0314000055",
    "BC040600F7033B000055",
]

END = [
    "BC0F010155",
    "BC11010455",
]

# The btsnoop showed exactly this pattern:
#   setup x3, then each data packet x3 with ~50-60ms gap, then end x3
SETUP_REPEAT = 3
DATA_REPEAT  = 3
SETUP_GAP    = 0.005     # 5ms between same-packet reps
DATA_INTRA_GAP = 0.005   # 5ms between reps of same data packet
DATA_INTER_GAP = 0.055   # ~55ms between different data packets
BIG_PAUSE    = 0.10      # gap between setup and data

async def main():
    print("PHONE BLUETOOTH MUST BE OFF. MR STAR APP MUST BE CLOSED.")
    input("Press Enter when ready...")

    async with BleakClient(ADDRESS, timeout=15.0) as client:
        print("Connected.")

        fff3 = None
        for svc in client.services:
            for ch in svc.characteristics:
                if "fff3" in ch.uuid.lower():
                    fff3 = ch.uuid
        if not fff3:
            print("FFF3 not found, aborting.")
            return
        print(f"Using {fff3}, response=False")

        # ---- 1. SETUP ----
        print("Sending SETUP...")
        for h in SETUP:
            for _ in range(SETUP_REPEAT):
                await client.write_gatt_char(fff3, bytes.fromhex(h), response=False)
                await asyncio.sleep(SETUP_GAP)

        await asyncio.sleep(BIG_PAUSE)

        # ---- 2. DATA ----
        print("Sending DATA (25 packets x3 each)...")
        for i, h in enumerate(DATA, 1):
            for _ in range(DATA_REPEAT):
                await client.write_gatt_char(fff3, bytes.fromhex(h), response=False)
                await asyncio.sleep(DATA_INTRA_GAP)
            await asyncio.sleep(DATA_INTER_GAP)
            print(f"  [{i:02d}/25] {h}")

        # ---- 3. END ----
        print("Sending END...")
        for h in END:
            for _ in range(SETUP_REPEAT):
                await client.write_gatt_char(fff3, bytes.fromhex(h), response=False)
                await asyncio.sleep(SETUP_GAP)

        print("\nFull sequence sent.")
        print("WATCH: did the strip enter Scroll and STAY there?")
        print("Keeping connection alive 15s so you can watch...")
        await asyncio.sleep(15)

asyncio.run(main())