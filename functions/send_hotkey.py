#!/usr/bin/env python3
"""Send a modifier+key combo via real XTest events, not AutoKey's
SendEvent-based keyboard.send_keys(). Window-manager-level global
shortcuts (Alt+F4, Alt+Tab, Super+Arrow, ...) are grabbed via XGrabKey
at the X server level and silently ignore SendEvent-based synthetic
keys - they need genuine XTest input like a real keyboard produces.

Usage: send_hotkey.py <Modifier1> [Modifier2 ...] <FinalKey> [--repeat N]
Keysym names are standard X11 names (case-sensitive), e.g.:
  Alt_L, Control_L, Shift_L, Super_L, F1..F35, Tab, Down, Up, Left, Right,
  or a plain lowercase letter like "c".

Examples:
  send_hotkey.py Alt_L F4
  send_hotkey.py Super_L Down
  send_hotkey.py Alt_L Tab --repeat 2
"""
import sys
import time
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest


def main():
    args = sys.argv[1:]
    repeat = 1
    if "--repeat" in args:
        i = args.index("--repeat")
        repeat = int(args[i + 1])
        del args[i:i + 2]

    hold_ms = 20
    if "--hold-ms" in args:
        i = args.index("--hold-ms")
        hold_ms = int(args[i + 1])
        del args[i:i + 2]

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    d = Display()
    codes = []
    for name in args:
        keysym = XK.string_to_keysym(name)
        if keysym == 0:
            print(f"Unbekanntes Keysym: {name}")
            sys.exit(1)
        codes.append(d.keysym_to_keycode(keysym))

    *mod_codes, key_code = codes

    # The keypad's physical combo (e.g. Ctrl+Alt+Shift+9) may still be
    # physically held when this script starts (the user hasn't released
    # the button yet), so those real modifiers can still be part of the
    # event state when we inject our own combo below - which makes a WM
    # grab expecting an EXACT mask (e.g. just Alt+F4) not match. Force a
    # clean slate first; releasing an already-up key is a harmless no-op.
    common_modifiers = ["Control_L", "Control_R", "Shift_L", "Shift_R",
                         "Alt_L", "Alt_R", "Super_L", "Super_R"]
    for name in common_modifiers:
        keysym = XK.string_to_keysym(name)
        if keysym:
            xtest.fake_input(d, X.KeyRelease, d.keysym_to_keycode(keysym))
    d.sync()
    time.sleep(0.05)

    for c in mod_codes:
        xtest.fake_input(d, X.KeyPress, c)
    d.sync()

    for _ in range(repeat):
        xtest.fake_input(d, X.KeyPress, key_code)
        d.sync()
        time.sleep(0.02)
        xtest.fake_input(d, X.KeyRelease, key_code)
        d.sync()
        time.sleep(0.02)

    # some WM gestures (e.g. Alt+Tab's window switcher) need the
    # modifier held a bit longer to register as a real hold, not just
    # a same-frame press+release blip
    time.sleep(hold_ms / 1000)

    for c in reversed(mod_codes):
        xtest.fake_input(d, X.KeyRelease, c)
    d.sync()


if __name__ == "__main__":
    main()
