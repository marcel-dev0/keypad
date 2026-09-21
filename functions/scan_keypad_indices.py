#!/usr/bin/env python3
"""Scan userlight key indices one at a time so a human can observe
which physical key/wheel lights up for each index. Also attempts to
read back the device's ACK report after each write for diagnostics."""
import glob
import os
import select
import subprocess
import sys
import time
from pathlib import Path

SET_COLOR = str(Path(__file__).resolve().parent / "set_keypad_color.py")
DELAY = 3.0

VENDOR_ID = "0816"
PRODUCT_ID = "2471"
VENDOR_INTERFACE_NUMBER = "02"


def find_hidraw():
    needle = f"v0000{VENDOR_ID}p0000{PRODUCT_ID}".lower()
    for uevent_path in glob.glob("/sys/class/hidraw/hidraw*/device/uevent"):
        with open(uevent_path) as f:
            content = f.read().lower()
        if needle not in content:
            continue
        device_dir = os.path.dirname(uevent_path)
        interface_dir = os.path.dirname(os.path.realpath(device_dir))
        try:
            with open(os.path.join(interface_dir, "bInterfaceNumber")) as f:
                iface_num = f.read().strip()
        except FileNotFoundError:
            continue
        if iface_num == VENDOR_INTERFACE_NUMBER:
            node = uevent_path.split("/sys/class/hidraw/")[1].split("/")[0]
            return f"/dev/{node}"
    raise SystemExit("hidraw device not found")


def try_read_ack(path, timeout=0.5):
    with open(path, "rb", buffering=0) as f:
        r, _, _ = select.select([f], [], [], timeout)
        if r:
            data = f.read(64)
            return data.hex()
    return None


start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 31
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1

hidraw = find_hidraw()
print(f"using {hidraw}")

subprocess.run([SET_COLOR, "effect", "userlight", "255", "0", "0"])  # saturated priming color,
# NOT (0,0,0): sat=0 makes the firmware fall back to an auto rainbow-cycle
print("ack:", try_read_ack(hidraw))

for i in range(start, end + 1, step):
    subprocess.run(["notify-send", "-t", str(int(DELAY * 1000)), "Keypad Scan", f"Index {i}"])
    # send twice: no confirmed ACK channel, so guard against a dropped write
    subprocess.run([SET_COLOR, "key", str(i), "255", "0", "0"])
    time.sleep(0.2)
    subprocess.run([SET_COLOR, "key", str(i), "255", "0", "0"])
    ack = try_read_ack(hidraw)
    print(f"index {i} ack: {ack}")
    time.sleep(DELAY)
    subprocess.run([SET_COLOR, "key", str(i), "0", "0", "0"])
    time.sleep(0.2)
    subprocess.run([SET_COLOR, "key", str(i), "0", "0", "0"])
    try_read_ack(hidraw)
    time.sleep(0.5)

subprocess.run(["notify-send", "Keypad Scan", "fertig"])
