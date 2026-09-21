import importlib
import sys
from pathlib import Path

_functions = str(Path(__file__).resolve().parent / "functions")
if _functions not in sys.path:
    sys.path.insert(0, _functions)
import keypad_config
importlib.reload(keypad_config)

import subprocess

layer = keypad_config.get_layer()
info = keypad_config.LAYERS.get(layer, {"name": "?", "keys": {}})
lines = [f"{n}: {info['keys'][n]['label']}" for n in sorted(info["keys"])]
subprocess.Popen(["notify-send", f"Layer {layer}: {info['name']}", "\n".join(lines)])
