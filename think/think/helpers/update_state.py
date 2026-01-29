import json

def update_battery_state_local_json(
    file_path: str,
    energy_mwh: float,
    capacity_mwh: float
):
    with open(file_path, "r") as f:
        data = json.load(f)

    soc_percent = (energy_mwh / capacity_mwh) * 100

    data["battery"]["energy_mwh"] = energy_mwh
    data["battery"]["soc_percent"] = soc_percent
    data["battery"]["capacity_mwh"] = capacity_mwh

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
