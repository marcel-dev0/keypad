"""Shared helpers for the keypad AutoKey scripts: layer state, debounce,
phrases and the step runner behind every Action N.py. The key assignments
themselves live in ../layers.py and are re-exported here as LAYERS, so
scripts only ever import keypad_config.
"""
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

FUNCTIONS_DIR = Path(__file__).resolve().parent
KEYPAD_DIR = FUNCTIONS_DIR.parent
if str(KEYPAD_DIR) not in sys.path:
    sys.path.insert(0, str(KEYPAD_DIR))

import layers
importlib.reload(layers)  # AutoKey caches imported modules; see Action N.py
LAYERS = layers.LAYERS
MAX_LAYER = layers.MAX_LAYER
LAYER_COLORS = layers.LAYER_COLORS

CACHE_DIR = Path.home() / ".cache"
STATE_FILE = CACHE_DIR / "keypad_layer"
DEBOUNCE_FILE = CACHE_DIR / "keypad_debounce.json"
PHRASES_FILE = KEYPAD_DIR / "phrases.json"


def get_layer():
    """AutoKey's `store` is scoped PER SCRIPT (persisted in that script's
    own .json), not shared across scripts - confirmed by inspecting the
    .json files directly (only the script that last called set_value had
    a non-empty store). A plain shared file is used instead so Layer Up,
    Layer Down, Show Layer and all Action N scripts see the same value."""
    try:
        return int(STATE_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 1


def set_layer(n):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(n))


def shift_layer(delta):
    """Move `delta` layers up (+1) or down (-1), wrapping around, and set
    the backlight to the new layer's colour."""
    layer = (get_layer() - 1 + delta) % MAX_LAYER + 1
    set_layer(layer)
    r, g, b = LAYER_COLORS[layer]
    subprocess.Popen([str(FUNCTIONS_DIR / "set_keypad_color.py"), "effect", "breath",
                      str(r), str(g), str(b), "--speed", "2", "--mono"])


DEBOUNCE_MS = 400


def should_fire(key_number):
    """The physical keypad buttons auto-repeat like any normal key when
    held down, firing the AutoKey hotkey (and this script) repeatedly.
    Each firing does a full modifier-release + combo-inject cycle, so a
    held button causes compounding/confusing repeats (e.g. closing then
    immediately acting on the next focused window). This makes even an
    accidental long hold count as a single action."""
    now = time.time()
    try:
        data = json.loads(DEBOUNCE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        data = {}
    last = data.get(str(key_number), 0)
    if (now - last) * 1000 < DEBOUNCE_MS:
        return False
    data[str(key_number)] = now
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DEBOUNCE_FILE.write_text(json.dumps(data))
    return True


def get_phrase(name):
    """Text for a ("phrase", name) step. phrases.json is re-read on every
    call (no module caching) and is kept out of git; its format is described
    in the README. On any error a desktop notification is shown and
    "DEFAULT" is returned (so that is what ends up being typed)."""
    try:
        phrases = json.loads(PHRASES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _notify_error(f"{PHRASES_FILE} fehlt - Aufbau siehe README")
        return "DEFAULT"
    except ValueError as e:
        _notify_error(f"{PHRASES_FILE} ist kein gültiges JSON: {e}")
        return "DEFAULT"
    try:
        return phrases[name]
    except (KeyError, TypeError):
        _notify_error(f"Phrase {name!r} fehlt in {PHRASES_FILE}")
        return "DEFAULT"


def _notify_error(message):
    subprocess.Popen(["notify-send", message])


def run_key(key_number, keyboard):
    """Execute the steps assigned to `key_number` on the current layer.
    `keyboard` is AutoKey's scripting object, only available in the
    script's own scope, so each Action N.py hands it in."""
    entry = LAYERS.get(get_layer(), {}).get("keys", {}).get(key_number)
    if not (entry and should_fire(key_number)):
        return
    for step in entry["value"]:
        kind = step[0]
        if kind == "hotkey":
            keys = step[1]
            opts = step[2] if len(step) > 2 else {}
            cmd = [str(FUNCTIONS_DIR / "send_hotkey.py"), *keys]
            if "repeat" in opts:
                cmd += ["--repeat", str(opts["repeat"])]
            if "hold_ms" in opts:
                cmd += ["--hold-ms", str(opts["hold_ms"])]
            subprocess.run(cmd)
        elif kind == "phrase":
            # via stdin, not argv: argv is world-readable in `ps`
            subprocess.run([str(FUNCTIONS_DIR / "type_text.py"), "--stdin"],
                           input=get_phrase(step[1]).encode("utf-8"))
        elif kind == "launch":
            subprocess.Popen(step[1], start_new_session=True)
        else:
            rest = list(step[1:])
            kwargs = rest.pop() if rest and isinstance(rest[-1], dict) else {}
            getattr(keyboard, kind)(*rest, **kwargs)
