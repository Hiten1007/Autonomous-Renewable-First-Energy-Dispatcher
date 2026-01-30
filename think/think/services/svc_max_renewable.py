from think.helpers.calculate_carbon_impact import calculate_carbon_impact

def execute_max_renewable(data):
    # data is a PhysicsSlice object, access via . not []
    solar = data.solar
    load = data.load
    current_energy = data.battery_energy
    cap = data.battery_capacity

    used_directly = min(solar, load)
    surplus_solar = max(0, solar - load)

    room_in_battery = cap - current_energy
    stored = min(surplus_solar, room_in_battery, 2.0)
    curtailed = surplus_solar - stored
    grid_import = max(0, load - used_directly)

    return {
        "solar": {"generated_mwh": solar, "used_directly_mwh": used_directly, "stored_mwh": stored, "curtailed_mwh": curtailed},
        "battery": {"state": "CHARGE" if stored > 0 else "IDLE", "soc_before_mwh": current_energy, "soc_after_mwh": current_energy + stored, "delta_mwh": stored},
        "supply_mix": {"local_renewables_mwh": used_directly, "grid_import_mwh": grid_import, "effective_re_percent": ((used_directly / load) * 100) if load > 0 else 0},
        # Note: PhysicsSlice doesn't have intensity, so we default to 0 or pass it separately
        "carbon": {"grid_intensity_gco2_per_kwh": 0, "saved_kgco2": 0, "actual_kgco2": 0, "baseline_kgco2": 0}
    }