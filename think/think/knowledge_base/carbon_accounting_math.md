# CARBON ACCOUNTING AND IMPACT MATHEMATICS

## BASELINE VS ACTUAL CARBON CALCULATION

### Baseline Scenario (No Battery, Grid Only)
- Formula: baseline_kgco2 = actual_load_mwh × (carbon_intensity_direct_gco2_per_kwh / 1000)
- This represents the carbon that would have been emitted if the entire load came from the grid.

### Actual Scenario (Agent-Optimized Mix)
- Formula: actual_kgco2 = grid_import_mwh × (carbon_intensity_direct_gco2_per_kwh / 1000)
- This represents the carbon actually emitted based on the agent's strategy.

### Carbon Savings
- Formula: saved_kgco2 = baseline_kgco2 - actual_kgco2
- A positive value means the agent successfully reduced carbon emissions.
- A negative value means the agent imported MORE from the grid than the baseline — this should never happen.

## CARBON INTENSITY THRESHOLDS (HARYANA / IN-NO REGION)

### Low Carbon (Clean Grid)
- carbon_intensity_direct_gco2_per_kwh < 400
- Typically occurs: 02:00 - 06:00 (night baseload with nuclear/hydro)
- Agent action: This is the best time for SVC_LOW_CARBON_GRID (grid charging).

### Medium Carbon
- carbon_intensity between 400 - 600
- Typically occurs: 08:00 - 16:00 (solar in the mix)
- Agent action: Prefer SVC_MAX_RENEWABLE if solar is available.

### High Carbon (Dirty Grid)
- carbon_intensity_direct_gco2_per_kwh > 600
- Typically occurs: 19:00 - 23:00 (coal peaking plants active in Haryana)
- Agent action: NEVER charge from grid. Discharge battery via SVC_PEAK_SHAVING.

### Critical Carbon
- carbon_intensity > 800
- Agent action: Call Safety_Protocol_Search immediately. Consider SVC_SAFE_THROTTLE if SOC is low.

## SUPPLY MIX INTEGRITY

### Effective Renewable Percentage Calculation
- Formula: effective_re_percent = ((local_renewables_mwh + (grid_import_mwh × renewable_percentage / 100)) / total_load) × 100
- local_renewables_mwh = solar used directly + battery discharge (if battery was charged via solar)

### Solar Balance Equation
- actual_solar_mwh = used_directly_mwh + stored_mwh + curtailed_mwh
- Must always sum correctly. If curtailed > 0, the agent failed to fully utilize solar.

## COAL_GAS AS A CARBON PROXY

### Using Load Data to Estimate Carbon
- The Haryana load data contains a "Coal_Gas" column (MWh generated from coal/gas plants).
- When Coal_Gas proportion in the total generation mix is increasing, carbon intensity is rising.
- Agent should cross-reference: if Coal_Gas > 3500 MWh, treat carbon intensity as HIGH (>600).