#!/usr/bin/env python3
"""Control the RGB lighting of the SDINNOVATION SIDE-KEYBOARD keypad
by replaying its HID output report formats, reverse engineered from
usbmon captures of the vendor's WebHID configurator.

Two independent report families exist, both sent as a 64-byte
interrupt OUT report to endpoint 3 (hidraw5). The device always
resends its FULL current state, so every field is required on write.

1) Effect report (style/off/static/breath/trigsingle/spectrum):
     06 0b 0b 00  00 01 00 <STYLE>  <SPEED> <MODE> 01 01  00 <HUE> <SAT> <VAL>  [pad]
   STYLE : 00 off, 01 static, 02 breath, 03 trigsingle, 04 spectrum, 05 userlight
   SPEED : effect speed, small integer (observed 1-4)
   MODE  : 02 default/rainbow, 03 "einfarbig" (fixed single color), 00 n/a (spectrum)
   HUE/SAT/VAL : HSV color, each 0-255 (not 0-360 for hue)

2) Per-key report (userlight only, one call per key):
     06 14 03 <BYTE_OFFSET>  00 00 00 00  <R> <G> <B>  00  [pad]
   BYTE_OFFSET : NOT a per-key id - it's a raw offset into a shared RGB
                 buffer, 3 bytes per key: offset = key_number * 3.
                 Confirmed against a physical 9-button scan (offsets
                 0,3,6,...,24 lit keys 1-9 in physical order; sending a
                 non-multiple-of-3 offset corrupts the neighbouring
                 key's colour since the 3-byte windows overlap).
   KEY_NUMBER  : 0-8, one of the 9 physical buttons. The keypad's 2
                 rotary wheels have no addressable RGB LED at all.
   R/G/B       : direct RGB, 0-255 each (confirmed against #ffa6f8 -> ff a6 f8)

There is also a "06 16 00 00 00 01 00 <STYLE>" style-select notification
the vendor tool sends before the effect report, but it is not required —
the effect report's own STYLE byte is sufficient on its own.
"""
import argparse
import colorsys
import glob
import os

VENDOR_ID = "0816"
PRODUCT_ID = "2471"
VENDOR_INTERFACE_NUMBER = "02"  # this device exposes 3 HID interfaces (0,1,2)
                                 # under the same VID:PID; only interface 2 accepts
                                 # the vendor lighting commands

STYLES = {
    "off": 0x00,
    "static": 0x01,
    "breath": 0x02,
    "trigsingle": 0x03,
    "spectrum": 0x04,
    "userlight": 0x05,
}


def find_hidraw():
    """Locate the keypad's hidraw node by VID/PID + USB interface number,
    instead of trusting a fixed /dev/hidrawN number (reassigned on every
    boot/reconnect) or matching VID/PID alone (this device exposes THREE
    hidraw nodes under the same VID/PID, one per HID interface - only
    interface 2 accepts the vendor lighting commands)."""
    needle = f"v0000{VENDOR_ID}p0000{PRODUCT_ID}".lower()
    for uevent_path in glob.glob("/sys/class/hidraw/hidraw*/device/uevent"):
        with open(uevent_path) as f:
            content = f.read().lower()
        if needle not in content:
            continue
        device_dir = os.path.dirname(uevent_path)
        interface_dir = os.path.dirname(os.path.realpath(device_dir))
        iface_num_path = os.path.join(interface_dir, "bInterfaceNumber")
        try:
            with open(iface_num_path) as f:
                iface_num = f.read().strip()
        except FileNotFoundError:
            continue
        if iface_num == VENDOR_INTERFACE_NUMBER:
            node = uevent_path.split("/sys/class/hidraw/")[1].split("/")[0]
            return f"/dev/{node}"
    raise SystemExit(
        f"Kein hidraw-Geraet fuer USB {VENDOR_ID}:{PRODUCT_ID} Interface "
        f"{VENDOR_INTERFACE_NUMBER} gefunden (Keypad angeschlossen? "
        "udev-Regel fuer plugdev vorhanden?)"
    )


def rgb_to_hsv_bytes(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return round(h * 255), round(s * 255), round(v * 255)


def send(report):
    with open(find_hidraw(), "wb") as f:
        f.write(report.ljust(64, b"\x00"))


def build_effect_report(style, speed, mono, r, g, b):
    hue, sat, val = rgb_to_hsv_bytes(r, g, b)
    mode = 0x03 if mono else 0x02
    return bytes([
        0x06, 0x0b, 0x0b, 0x00,
        0x00, 0x01, 0x00,
        STYLES[style],
        speed,
        mode,
        0x01, 0x01,
        0x00,
        hue, sat, val,
    ])


NUM_KEYS = 9


def build_key_report(key_number, r, g, b):
    byte_offset = key_number * 3
    return bytes([
        0x06, 0x14, 0x03, byte_offset,
        0x00, 0x00, 0x00, 0x00,
        r, g, b,
        0x00,
    ])


def main():
    p = argparse.ArgumentParser(description="Control SDINNOVATION keypad RGB lighting")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("effect", help="set a global lighting style/color")
    pe.add_argument("style", choices=STYLES)
    pe.add_argument("r", type=int)
    pe.add_argument("g", type=int)
    pe.add_argument("b", type=int)
    pe.add_argument("--speed", type=int, default=1)
    pe.add_argument("--mono", action="store_true",
                     help='set the "einfarbig" (fixed single color) flag')

    pk = sub.add_parser("key", help="set an individual key's color (userlight mode)")
    pk.add_argument("number", type=int, choices=range(NUM_KEYS), help="0-8, physical key number")
    pk.add_argument("r", type=int)
    pk.add_argument("g", type=int)
    pk.add_argument("b", type=int)

    args = p.parse_args()

    if args.cmd == "effect":
        report = build_effect_report(args.style, args.speed, args.mono, args.r, args.g, args.b)
        send(report)
        print(f"effect style={args.style} speed={args.speed} mono={args.mono} rgb=({args.r},{args.g},{args.b})")
    elif args.cmd == "key":
        report = build_key_report(args.number, args.r, args.g, args.b)
        send(report)
        print(f"key number={args.number} (byte offset {args.number*3}) rgb=({args.r},{args.g},{args.b})")


if __name__ == "__main__":
    main()
