from think.helpers.calculate_carbon_impact import calculate_carbon_impact

def execute_safe_throttle(data):
    # data is a PhysicsSlice object
    solar = data.solar
    load = data.load
    current_energy = data.battery_energy

    used_directly = min(solar, load)
    grid_import = load - used_directly

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": 0, "curtailed_mwh": 0},
        "battery": {"state": "STANDBY", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy, "delta_mwh": 0},
        "supply_mix": {"local_renewables_mwh": used_directly, "grid_import_mwh": grid_import, "effective_re_percent": (used_directly / load) * 100 if load > 0 else 0},
        "carbon": {"grid_intensity_gco2_per_kwh": 0, "saved_kgco2": 0, "actual_kgco2": 0, "baseline_kgco2": 0}
    }