import json
from pathlib import Path

# 1. Get the path of the current file (update_state.py)
current_file = Path(__file__).resolve()

# 2. Go up the levels to reach the project root
# update_state.py is in think/helpers/, so:
# .parent = helpers/
# .parent.parent = think/
# .parent.parent.parent = Root (Autonomous Renewable First Energy Dispatcher)
root_dir = current_file.parent.parent.parent

# 3. Target the file in the root
FILE_PATH = root_dir / "battery_state.json"

def update_battery_state_local_json(new_energy, capacity):
    # Calculate SOC dynamically from the data passed in
    new_soc = (new_energy / capacity) * 100
    
    state = {
        "energy_mwh": round(new_energy, 2),
        "capacity_mwh": capacity,
        "soc_percent": round(new_soc, 2)
    }

    try:
        with open(FILE_PATH, "w") as f:
            json.dump(state, f, indent=4)
        print(f"✅ Battery State Persisted to: {FILE_PATH.name}")
    except Exception as e:
        print(f"❌ Critical Persistence Failure: {e}")