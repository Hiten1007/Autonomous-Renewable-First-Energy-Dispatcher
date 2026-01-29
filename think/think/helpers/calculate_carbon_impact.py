def calculate_carbon_impact(grid_import_mwh, actual_load_mwh, grid_intensity):
    # Baseline: What if we only used the grid?
    baseline_kg = actual_load_mwh * grid_intensity
    # Actual: What we are actually importing now
    actual_kg = grid_import_mwh * grid_intensity
    return {
        "grid_intensity_gco2_per_kwh": grid_intensity,
        "baseline_kgco2": round(baseline_kg, 2),
        "actual_kgco2": round(actual_kg, 2),
        "saved_kgco2": round(baseline_kg - actual_kg, 2)
    }