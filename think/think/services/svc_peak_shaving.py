from think.helpers.calculate_carbon_impact import calculate_carbon_impact

def execute_peak_shaving(data):
    # data is a CarbonSlice object
    solar = data.solar
    load = data.load
    current_energy = data.battery_energy

    used_directly = min(solar, load)
    load_gap = load - used_directly
    
    usable_energy = max(0, current_energy - (data.battery_capacity * 0.20))
    discharged = min(load_gap, usable_energy, 2.5)
    grid_import = load_gap - discharged

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": 0, "curtailed_mwh": 0},
        "battery": {"state": "DISCHARGE" if discharged > 0 else "IDLE", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy - discharged, "delta_mwh": -discharged},
        "supply_mix": {"local_renewables_mwh": used_directly + discharged, "grid_import_mwh": grid_import, "effective_re_percent": (((used_directly + discharged) / load) * 100) if load > 0 else 0},
        "carbon": calculate_carbon_impact(grid_import, load, data.grid_intensity)
    }