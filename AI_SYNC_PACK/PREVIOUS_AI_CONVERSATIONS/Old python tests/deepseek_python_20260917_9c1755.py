import asyncio
from bleak import BleakClient

# ============================================================
# YOUR STRIPS - replace or add MAC addresses if needed
# ============================================================
STRIPS = [
    "41:42:59:F1:C8:68",
    "41:42:43:E7:8B:F6",
    "41:42:F9:D7:45:B0",
]

# ============================================================
# EXACT MR STAR SCROLL SEQUENCE (captured from your bugreport)
# ============================================================
SCROLL_SETUP = [
    "BC0F010155",
    "BC11010455",
]

SCROLL_DATA = [
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

SCROLL_END = [
    "BC0F010155",
    "BC11010455",
]

# ============================================================
# STANDARD COMMANDS (fallback for simple on/off/color)
# ============================================================
CMD_ON  = "cc2333"
CMD_OFF = "cc2433"

def color_cmd(r, g, b):
    return f"56{r:02X}{g:02X}{b:02X}00f0aa"


# ============================================================
# STRIP CLASS
# ============================================================
class Strip:
    def __init__(self, mac):
        self.mac = mac
        self.client = None
        self.handle = None

    async def connect(self):
        self.client = BleakClient(self.mac, timeout=15.0)
        await self.client.connect()
        if not self.client.is_connected:
            raise Exception("not connected")

        # Find the write characteristic (usually FFF3)
        for service in self.client.services:
            for char in service.characteristics:
                if "fff3" in char.uuid.lower() and "write" in char.properties:
                    self.handle = char.handle
                    break
            if self.handle:
                break

        if self.handle is None:
            raise Exception("No FFF3 write handle found")

        print(f"[{self.mac}] connected, write handle = {self.handle}")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def send(self, hexstr, repeat=1, delay=0.05):
        if not self.client or not self.client.is_connected:
            print(f"[{self.mac}] not connected")
            return
        data = bytes.fromhex(hexstr)
        for _ in range(repeat):
            await self.client.write_gatt_char(self.handle, data, response=False)
            await asyncio.sleep(0.005)
        await asyncio.sleep(delay)

    async def send_scroll(self):
        print(f"[{self.mac}] sending MR Star Scroll sequence...")
        # Setup
        for p in SCROLL_SETUP:
            await self.send(p, repeat=3, delay=0.01)
        await asyncio.sleep(0.1)
        # Main scroll data
        for p in SCROLL_DATA:
            await self.send(p, repeat=3, delay=0.05)
        # End
        for p in SCROLL_END:
            await self.send(p, repeat=3, delay=0.01)
        print(f"[{self.mac}] Scroll sequence sent.")


# ============================================================
# MAIN MENU
# ============================================================
async def main():
    strips = [Strip(mac) for mac in STRIPS]
    connected = []

    print("Connecting to strips...")
    for s in strips:
        try:
            await s.connect()
            connected.append(s)
        except Exception as e:
            print(f"Failed to connect {s.mac}: {e}")

    if not connected:
        print("No strips connected. Exiting.")
        return

    while True:
        print("\n" + "=" * 50)
        print("MR Star LED Controller")
        print("=" * 50)
        print("1. Turn ON")
        print("2. Turn OFF")
        print("3. Set Color (R G B)")
        print("4. Activate MR Star Scroll (exact capture)")
        print("5. Send Custom Hex")
        print("6. Disconnect and Quit")
        print("=" * 50)

        choice = input("Choose: ").strip()

        if choice == "1":
            for s in connected:
                await s.send(CMD_ON, repeat=3, delay=0.05)
            print("ON sent.")

        elif choice == "2":
            for s in connected:
                await s.send(CMD_OFF, repeat=3, delay=0.05)
            print("OFF sent.")

        elif choice == "3":
            try:
                r, g, b = map(int, input("Enter R G B (0-255): ").split())
                cmd = color_cmd(r, g, b)
                for s in connected:
                    await s.send(cmd, repeat=3, delay=0.05)
                print(f"Color sent: {cmd}")
            except Exception as e:
                print("Invalid input:", e)

        elif choice == "4":
            for s in connected:
                await s.send_scroll()
            print("Scroll sequence sent to all connected strips.")

        elif choice == "5":
            hexstr = input("Enter hex string (no spaces): ").strip()
            for s in connected:
                await s.send(hexstr, repeat=3, delay=0.05)
            print("Custom hex sent.")

        elif choice == "6":
            for s in connected:
                await s.disconnect()
            print("Disconnected. Bye.")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")