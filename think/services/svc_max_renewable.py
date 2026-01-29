from think.helpers.calculate_carbon_impact import calculate_carbon_impact
def execute_max_renewable(data):
    solar = data['current_state']['actual_solar_mwh']
    load = data['current_state']['actual_load_mwh']
    soc = data['current_state']['battery']['soc_percent']
    cap = data['current_state']['battery']['capacity_mwh']
    current_energy = data['current_state']['battery']['energy_mwh']

    # 1. Direct Usage
    used_directly = min(solar, load)
    surplus_solar = max(0, solar - load)

    # 2. Storage (Charging)
    room_in_battery = cap - current_energy
    # Max charge rate limit (e.g., 2.0 MWh per window from your KB)
    stored = min(surplus_solar, room_in_battery, 2.0)
    
    # 3. Curtailment
    curtailed = surplus_solar - stored
    
    # 4. Grid Gap
    grid_import = max(0, load - used_directly)

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": stored, "curtailed_mwh": curtailed},
        "battery": {"state": "CHARGE" if stored > 0 else "IDLE", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy + stored, "delta_mwh": stored},
        "supply_mix": {"local_renewables_mwh": used_directly, "grid_import_mwh": grid_import, "effective_re_percent": ((used_directly / load) * 100) if load > 0 else 100},
        "carbon": calculate_carbon_impact(grid_import, load, data['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    }

