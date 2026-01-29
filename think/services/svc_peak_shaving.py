from think.helpers.calculate_carbon_impact import calculate_carbon_impact

def execute_peak_shaving(data):
    solar = data['current_state']['actual_solar_mwh']
    load = data['current_state']['actual_load_mwh']
    current_energy = data['current_state']['battery']['energy_mwh']
    soc = data['current_state']['battery']['soc_percent']

    used_directly = min(solar, load)
    load_gap = load - used_directly
    
    # 1. Discharge Logic (Stop at 20% SoC safety floor)
    usable_energy = max(0, current_energy - (data['current_state']['battery']['capacity_mwh'] * 0.20))
    # Max discharge rate limit (e.g., 2.5 MWh per window)
    discharged = min(load_gap, usable_energy, 2.5)
    
    grid_import = load_gap - discharged

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": 0, "curtailed_mwh": 0},
        "battery": {"state": "DISCHARGE" if discharged > 0 else "IDLE", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy - discharged, "delta_mwh": -discharged},
        "supply_mix": {"local_renewables_mwh": used_directly + discharged, "grid_import_mwh": grid_import, "effective_re_percent": (((used_directly + discharged) / load) * 100)},
        "carbon": calculate_carbon_impact(grid_import, load, data['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    }