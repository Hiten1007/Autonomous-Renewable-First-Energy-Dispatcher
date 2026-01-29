from think.helpers.calculate_carbon_impact import calculate_carbon_impact

def execute_low_carbon_grid(data):
    solar = data['current_state']['actual_solar_mwh']
    load = data['current_state']['actual_load_mwh']
    current_energy = data['current_state']['battery']['energy_mwh']
    cap = data['current_state']['battery']['capacity_mwh']

    used_directly = min(solar, load)
    
    # 1. Charging from Grid (Stop at 70% to leave room for solar)
    target_energy = cap * 0.70
    charge_needed = max(0, target_energy - current_energy)
    charge_amount = min(charge_needed, 2.0) # Max charge rate
    
    grid_import = (load - used_directly) + charge_amount

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": 0, "curtailed_mwh": 0},
        "battery": {"state": "CHARGE", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy + charge_amount, "delta_mwh": charge_amount},
        "supply_mix": {"local_renewables_mwh": used_directly, "grid_import_mwh": grid_import, "effective_re_percent": (used_directly / load) * 100},
        "carbon": calculate_carbon_impact(grid_import, load, data['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    }