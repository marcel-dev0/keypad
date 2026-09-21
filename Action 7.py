import importlib
import sys
from pathlib import Path

_functions = str(Path(__file__).resolve().parent / "functions")
if _functions not in sys.path:
    sys.path.insert(0, _functions)
import keypad_config
importlib.reload(keypad_config)

keypad_config.run_key(7, keyboard)
