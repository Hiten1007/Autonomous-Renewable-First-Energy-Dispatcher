import json
from pathlib import Path

current_file = Path(__file__).resolve()

root_dir = current_file.parent.parent.parent

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