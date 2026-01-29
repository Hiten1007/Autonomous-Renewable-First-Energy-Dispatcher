from think.helpers.calculate_carbon_impact import calculate_carbon_impact
def execute_safe_throttle(data):
    solar = data['current_state']['actual_solar_mwh']
    load = data['current_state']['actual_load_mwh']
    current_energy = data['current_state']['battery']['energy_mwh']

    used_directly = min(solar, load)
    grid_import = load - used_directly

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": 0, "curtailed_mwh": 0},
        "battery": {"state": "STANDBY", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy, "delta_mwh": 0},
        "supply_mix": {"local_renewables_mwh": used_directly, "grid_import_mwh": grid_import, "effective_re_percent": (used_directly / load) * 100},
        "carbon": calculate_carbon_impact(grid_import, load, data['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    }