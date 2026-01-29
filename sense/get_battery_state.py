import json
from pathlib import Path

BATTERY_FILE = Path("../battery_state.json")

def get_battery_state():
    with open(BATTERY_FILE, "r") as f:
        return json.load(f)