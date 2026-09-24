"""Wait until no key is physically held down any more.

AutoKey fires on key PRESS, so while type_text.py / send_hotkey.py run,
the keypad's combo (Ctrl+Alt+Shift+N) is usually still held. After the
X auto-repeat delay (`xset q`, 500 ms here) the keypad's repeat events
re-assert those modifiers, and everything injected from then on arrives
as Ctrl+Alt+Shift+<key> - apps treat that as a shortcut and drop it, so
a long press cut typed text off after ~15 characters. Releasing the
modifiers via XTest does not help: XTest can only release keys pressed
through XTest, not the ones held on the physical device.
"""
import time

POLL_S = 0.01


def wait_for_release(display, timeout_s=5.0):
    """Block until the X server reports no pressed keys, or `timeout_s`
    has passed (then carry on anyway rather than never acting)."""
    deadline = time.monotonic() + timeout_s
    while any(display.query_keymap()) and time.monotonic() < deadline:
        time.sleep(POLL_S)
