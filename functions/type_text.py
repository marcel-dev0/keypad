#!/usr/bin/env python3
"""Type literal text via real XTest events, not AutoKey's SendEvent-based
keyboard.send_keys(). Some targets only accept genuine X server input and
silently ignore synthetic SendEvent keys - e.g. Cinnamon's own modal
"Legitimation erforderlich" (polkit) dialog, which lives inside the
cinnamon process and holds the keyboard grab.

Usage: type_text.py <text> [--delay-ms N]
       type_text.py --stdin [--delay-ms N]     (UTF-8 text from stdin)

Use --stdin for secrets: command-line arguments are visible to every
local user in `ps`.

Each character is mapped to a keycode + shift level via the current
keyboard layout (column 1 = Shift, 4 = AltGr, 5 = AltGr+Shift), so uppercase,
umlauts and symbols work as on a real keyboard.
"""
import sys
import time
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

from wait_for_release import wait_for_release

# Column in the keycode's keysym table -> modifiers needed. Columns 2/3
# are the second layout group (would need a group switch) and are left out.
LEVEL_MODIFIERS = {
    0: [],
    1: ["Shift_L"],
    4: ["ISO_Level3_Shift"],
    5: ["ISO_Level3_Shift", "Shift_L"],
}


def main():
    args = sys.argv[1:]
    delay_ms = 15
    if "--delay-ms" in args:
        i = args.index("--delay-ms")
        delay_ms = int(args[i + 1])
        del args[i:i + 2]

    if "--stdin" in args:
        args.remove("--stdin")
        if args:
            print(__doc__)
            sys.exit(1)
        text = sys.stdin.buffer.read().decode("utf-8")
    elif len(args) == 1:
        text = args[0]
    else:
        print(__doc__)
        sys.exit(1)

    d = Display()
    # python-xlib only knows latin1 + miscellany keysym names by default;
    # ISO_Level3_Shift (AltGr) lives in the xkb group.
    XK.load_keysym_group("xkb")

    def keycode(name):
        return d.keysym_to_keycode(XK.string_to_keysym(name))

    for name in {m for mods in LEVEL_MODIFIERS.values() for m in mods}:
        if not keycode(name):
            print(f"Modifier {name} hat keinen Keycode im aktuellen Layout")
            sys.exit(1)

    # Resolve everything before sending anything, so an untypable
    # character aborts cleanly instead of leaving half the text typed.
    plan = []
    for ch in text:
        # Latin-1 keysyms equal the code point; others are either a legacy
        # keysym (e.g. EuroSign = 0x20AC) or a Unicode keysym (0x01000000+).
        candidates = []
        for keysym in (ord(ch), 0x01000000 + ord(ch)):
            candidates = d.keysym_to_keycodes(keysym)
            if candidates:
                break
        if not candidates:
            print(f"Zeichen {ch!r} ist im aktuellen Layout nicht tippbar")
            sys.exit(1)
        code, level = min(candidates, key=lambda c: c[1])
        if level not in LEVEL_MODIFIERS:
            print(f"Zeichen {ch!r}: Ebene {level} wird nicht unterstuetzt")
            sys.exit(1)
        plan.append((code, [keycode(m) for m in LEVEL_MODIFIERS[level]]))

    # The keypad's own combo (Ctrl+Alt+Shift+N) may still be physically
    # held; those modifiers would end up in the state of every typed key.
    # Wait for the button to be let go (see wait_for_release.py), then
    # release them once more in case the wait timed out. Releasing an
    # already-up key is a harmless no-op. See send_hotkey.py.
    wait_for_release(d)
    for name in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L",
                 "Alt_R", "Super_L", "Super_R", "ISO_Level3_Shift"]:
        code = keycode(name)
        if code:
            xtest.fake_input(d, X.KeyRelease, code)
    d.sync()
    time.sleep(0.05)

    # Small pauses between modifier press, key press and release: without
    # them the receiving app's input pipeline occasionally reordered
    # neighbouring characters (seen with GTK, e.g. "Ä " typed as " Ä").
    step = delay_ms / 1000
    for code, mods in plan:
        for m in mods:
            xtest.fake_input(d, X.KeyPress, m)
        if mods:
            d.sync()
            time.sleep(step)
        xtest.fake_input(d, X.KeyPress, code)
        d.sync()
        time.sleep(step)
        xtest.fake_input(d, X.KeyRelease, code)
        for m in reversed(mods):
            xtest.fake_input(d, X.KeyRelease, m)
        d.sync()
        time.sleep(step)


if __name__ == "__main__":
    main()
