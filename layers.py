"""Key assignments of the keypad - the only file to edit when changing them.

Each layer has a theme "name" and a "keys" dict (1-9) with a display
"label" (used by Show Layer.py) and a "value": a list of steps,
executed in order by Action N.py. Four step kinds:

- ("send_keys", "...")  -> keyboard.send_keys(...). Fine for APP-INTERNAL
  shortcuts (the focused app itself reads the key, e.g. Ctrl+C/V/X in
  most programs). Text is parsed: "<ctrl>" etc. are special keys.
- ("phrase", "name") -> types the text stored under "name" in
  phrases.json (format: see README; the file is git-ignored)
  via real XTest events (type_text.py), passed through stdin so secrets
  never show up in `ps`. Works where send_keys is ignored, e.g. Cinnamon's
  modal "Legitimation erforderlich" (polkit) dialog. Limits: no
  newlines/tabs/emoji.
- ("launch", ["program", "arg", ...]) -> starts a program detached from
  AutoKey (does not wait for it to exit), e.g. ["firefox", "https://..."].
- ("hotkey", [Keysyms...], {"repeat": 1, "hold_ms": 20}) -> shells out to
  send_hotkey.py, which sends real XTest events instead
  of AutoKey's SendEvent-based send_keys. REQUIRED for window-manager
  -level GLOBAL shortcuts (Alt+F4, Alt+Tab, Super+Arrow, ...): those
  are caught via XGrabKey at the X server level and silently ignore
  SendEvent-based synthetic keys, so send_keys looks like it does
  nothing for them even though no error is raised. Confirmed by
  reading AutoKey's own interface.py (send_modified_key uses
  XSendEvent, not XTest) and reproducing the bug/fix live.
  Keysym names are the standard X11 names (case-sensitive), e.g.
  "Alt_L", "Control_L", "Super_L", "F4", "Tab", "Down", "Up", "c".
"""

import os

_FUNCTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "functions")
_SET_KEYPAD_COLOR = os.path.join(_FUNCTIONS_DIR, "set_keypad_color.py")

TODO_KEY = {"label": "TODO", "value": []}


def _todo_layer(name):
    return {"name": name, "keys": {n: dict(TODO_KEY) for n in range(1, 10)}}


LAYERS = {
    1: {
        "name": "Mail",
        "keys": {
            1: {"label": "Outlook", "value": [("launch", ["firefox", "https://outlook.live.com/mail/"])]},
            2: dict(TODO_KEY),
            3: dict(TODO_KEY),
            4: {"label": "Danke-Antwort", "value": [("phrase", "danke")]},
            5: dict(TODO_KEY),
            6: dict(TODO_KEY),
            7: dict(TODO_KEY),
            8: dict(TODO_KEY),
            9: dict(TODO_KEY),
        },
    },
    2: {
        "name": "Fenster",
        "keys": {
            1: {"label": "pass", "value": [("phrase", "passwort")]},
            2: dict(TODO_KEY),
            3: dict(TODO_KEY),
            4: {"label": "Alt+Tab", "value": [("hotkey", ["Alt_L", "Tab"], {"hold_ms": 200})]},
            5: {"label": "Alt+Tab (2x)", "value": [("hotkey", ["Alt_L", "Tab"], {"repeat": 2, "hold_ms": 200})]},
            6: dict(TODO_KEY),
            7: {"label": "Minimieren", "value": [("hotkey", ["Super_L", "h"])]},
            8: {"label": "Maximieren", "value": [("hotkey", ["Super_L", "Up"])]},
            9: {"label": "Schließen", "value": [("hotkey", ["Alt_L", "F4"])]},
        },
    },
    3: {
        "name": "Copy/Paste",
        "keys": {
            1: dict(TODO_KEY),
            2: dict(TODO_KEY),
            3: dict(TODO_KEY),
            4: {"label": "Ausschneiden", "value": [("send_keys", "<ctrl>+x")]},
            5: {"label": "Kopieren", "value": [("send_keys", "<ctrl>+c")]},
            6: {"label": "Einfügen", "value": [("send_keys", "<ctrl>+v")]},
            7: dict(TODO_KEY),
            8: dict(TODO_KEY),
            9: dict(TODO_KEY),
        },
    },
    4: {
        "name": "YouTube",
        "keys": {
            1: {"label": "YouTube", "value": [("launch", ["brave-browser", "https://www.youtube.com"])]},
            # YouTube: Shift+, / Shift+. = +-0.25x per press (0.25x..2x), so
            # run to the 0.25x stop first, then step up to the target speed
            2: {"label": "1x", "value": [("hotkey", ["Shift_L", "comma"], {"repeat": 7}),
                                         ("hotkey", ["Shift_L", "period"], {"repeat": 3})]},
            3: {"label": "2x", "value": [("hotkey", ["Shift_L", "period"], {"repeat": 7})]},
            4: dict(TODO_KEY),
            5: dict(TODO_KEY),
            6: dict(TODO_KEY),
            7: dict(TODO_KEY),
            8: dict(TODO_KEY),
            9: {"label": "Licht aus", "value": [("launch", [_SET_KEYPAD_COLOR, "effect", "off", "0", "0", "0"])]},
        },
    },
    5: {
        "name": "VS Code",
        "keys": {
            1: {"label": "VSCode", "value": [("launch", ["code", ""])]},
            2: {"label": "Checkout dev", "value": [("phrase", "checkout")]},
            3: {"label": "Pull dev", "value": [("phrase", "pull")]},
            4: {"label": "Merge", "value": [("phrase", "merge")]},
            5: {"label": "Main", "value": [("phrase", "main")]},
            6: dict(TODO_KEY),
            7: dict(TODO_KEY),
            8: dict(TODO_KEY),
            9: dict(TODO_KEY),
        },
    },
    6: _todo_layer("TODO"),
}

MAX_LAYER = len(LAYERS)

# Backlight colour (R, G, B) per layer, set by Layer Up.py / Layer Down.py
LAYER_COLORS = {
    1: (255, 255, 0),    # Gelb
    2: (0, 255, 255),    # Cyan
    3: (0, 255, 0),      # Gruen
    4: (255, 0, 0),      # Rot
    5: (0, 0, 255),      # Blau
    6: (255, 0, 255),    # Magenta
}
