import asyncio
from bleak import BleakClient

# ============================================================
# YOUR STRIPS
# ============================================================
STRIPS = [
    "41:42:59:F1:C8:68",
    "41:42:43:E7:8B:F6",
    "41:42:F9:D7:45:B0",
]

# ============================================================
# VERIFIED WORKING COMMANDS (unchanged from RGB_script_working.py)
# ============================================================
CMD_ON  = "cc2333"
CMD_OFF = "cc2433"

def color_cmd(r, g, b):
    return f"56{r:02X}{g:02X}{b:02X}00f0aa"

SCROLL_SETUP = ["BC0F010155", "BC11010455"]
SCROLL_DATA = [
    "BC0406000003E8000055", "BC0406013E0032000055", "BC04060131002B000055",
    "BC040600E200A8000055", "BC040600E400B8000055", "BC040600E60091000055",
    "BC040600E90046000055", "BC040600F00027000055", "BC040600F00023000055",
    "BC040600F00023000055", "BC040600FF003E000055", "BC040601050081000055",
    "BC0406011B00EB000055", "BC0406013D01A3000055", "BC0406014D0230000055",
    "BC04060161026F000055", "BC0406001B02FC000055", "BC0406002C0372000055",
    "BC0406003E02E1000055", "BC0406005A0215000055", "BC0406008701BF000055",
    "BC040600B00215000055", "BC040600C90296000055", "BC040600DF0314000055",
    "BC040600F7033B000055",
]
SCROLL_END = ["BC0F010155", "BC11010455"]

# ============================================================
# NEW - CANDIDATE COMMANDS FOUND IN THE FULL btsnoop CAPTURE
# (not yet confirmed against the physical strip - test with option 7/8/9)
#
#   BC11 01 XX 55   -- XX in {01,02,03,04}. 04 is CONFIRMED = Scroll
#                      (it's literally what SCROLL_SETUP/END send).
#                      01/02/03 are UNTESTED candidate pattern slots.
#   BC06 02 00 XX 55 -- XX ranged over {01,02,03,04,07,0A,1B,1D,1E,20}
#                      while the phone's UI was being used (looked like
#                      a slider drag). Strong candidate for speed or
#                      brightness. Range/meaning UNCONFIRMED.
#   BC0F 01 XX 55    -- XX in {00,01}. Seen bracketing BC11 selections.
#                      Candidate "commit/apply" or "edit mode" flag.
#   BC01 01 XX 55    -- XX in {00,01}. Simple toggle, purpose unknown.
#   BC09 06 .. ..    -- same 10-byte shape as the BC04 data frames,
#                      always ending in 03E8000055. Seen alongside mode
#                      switches. Possibly a "preview color" companion
#                      to a BC04 stream. Purpose unclear.
# ============================================================

def mode_cmd(n):
    """Candidate: select built-in pattern slot n (1-4 seen so far)."""
    return f"BC1101{n:02X}55"

def speed_cmd(n):
    """Candidate: set a speed/brightness parameter (0-~50 range seen)."""
    return f"BC060200{n:02X}55"

def flag0f_cmd(n):
    """Candidate: BC0F apply/commit flag (0 or 1 seen)."""
    return f"BC0F01{n:02X}55"

def flag01_cmd(n):
    """Candidate: BC01 toggle (0 or 1 seen)."""
    return f"BC0101{n:02X}55"


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
        try:
            data = bytes.fromhex(hexstr)
        except ValueError:
            print(f"[{self.mac}] invalid hex: {hexstr}")
            return
        for _ in range(repeat):
            await self.client.write_gatt_char(self.handle, data, response=False)
            await asyncio.sleep(0.005)
        await asyncio.sleep(delay)

    async def send_scroll(self):
        print(f"[{self.mac}] sending Scroll sequence...")
        for p in SCROLL_SETUP:
            await self.send(p, repeat=3, delay=0.01)
        await asyncio.sleep(0.1)
        for p in SCROLL_DATA:
            await self.send(p, repeat=3, delay=0.055)
        for p in SCROLL_END:
            await self.send(p, repeat=3, delay=0.01)
        print(f"[{self.mac}] Scroll sequence sent.")


async def broadcast(strips, method, *args, **kwargs):
    tasks = [getattr(s, method)(*args, **kwargs) for s in strips]
    await asyncio.gather(*tasks)


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
        print("\n" + "=" * 60)
        print("MR Star LED Controller v2")
        print("=" * 60)
        print(" 1. Turn ON")
        print(" 2. Turn OFF")
        print(" 3. Set Color (R G B)")
        print(" 4. Activate Scroll (verified exact capture)")
        print(" 5. Send Custom Hex")
        print(" --- exploring the new opcodes found in the log ---")
        print(" 6. Try mode slot N        (BC11 01 N 55, N=1..4+)")
        print(" 7. Try speed/param N      (BC06 02 00 N 55, N=0..50ish)")
        print(" 8. Try BC0F flag (0/1)")
        print(" 9. Try BC01 flag (0/1)")
        print(" 0. Quit")
        print("=" * 60)

        choice = input("Choose: ").strip().lower()

        if choice in ("1", "on"):
            await broadcast(connected, "send", CMD_ON, repeat=3, delay=0.05)
            print("ON sent.")

        elif choice in ("2", "off"):
            await broadcast(connected, "send", CMD_OFF, repeat=3, delay=0.05)
            print("OFF sent.")

        elif choice in ("3", "color"):
            try:
                r, g, b = map(int, input("R G B (0-255): ").replace(",", " ").split())
                await broadcast(connected, "send", color_cmd(r, g, b), repeat=3, delay=0.05)
                print("Color sent.")
            except ValueError:
                print("Invalid input.")

        elif choice in ("4", "scroll"):
            await broadcast(connected, "send_scroll")
            print("Scroll sequence sent.")

        elif choice in ("5", "hex"):
            hexstr = input("Hex string (no spaces): ").strip()
            try:
                bytes.fromhex(hexstr)
            except ValueError:
                print("Invalid hex.")
                continue
            await broadcast(connected, "send", hexstr, repeat=3, delay=0.05)
            print("Custom hex sent.")

        elif choice == "6":
            try:
                n = int(input("Mode slot number to try (e.g. 1,2,3,4): "))
                cmd = mode_cmd(n)
                print(f"Sending {cmd} -- WATCH THE STRIP now.")
                await broadcast(connected, "send", cmd, repeat=3, delay=0.05)
            except ValueError:
                print("Invalid number.")

        elif choice == "7":
            try:
                n = int(input("Speed/param value to try (e.g. 0-50): "))
                cmd = speed_cmd(n)
                print(f"Sending {cmd} -- WATCH THE STRIP now.")
                await broadcast(connected, "send", cmd, repeat=3, delay=0.05)
            except ValueError:
                print("Invalid number.")

        elif choice == "8":
            try:
                n = int(input("BC0F flag value (0 or 1): "))
                cmd = flag0f_cmd(n)
                print(f"Sending {cmd} -- WATCH THE STRIP now.")
                await broadcast(connected, "send", cmd, repeat=3, delay=0.05)
            except ValueError:
                print("Invalid number.")

        elif choice == "9":
            try:
                n = int(input("BC01 flag value (0 or 1): "))
                cmd = flag01_cmd(n)
                print(f"Sending {cmd} -- WATCH THE STRIP now.")
                await broadcast(connected, "send", cmd, repeat=3, delay=0.05)
            except ValueError:
                print("Invalid number.")

        elif choice in ("0", "quit", "exit", "q"):
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
