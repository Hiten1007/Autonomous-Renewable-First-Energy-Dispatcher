# CARBON IMPACT AND ACCOUNTING MATHEMATICS
## [CALC-01] Baseline vs Actual
- **Baseline Scenario**: A world where the battery does not exist. 
  - `baseline_kgco2 = actual_load_mwh * (grid_intensity / 1000)`
- **Actual Scenario**: The real mix chosen by the agent.
  - `actual_kgco2 = grid_import_mwh * (grid_intensity / 1000)`
- **Savings**: `saved_kgco2 = baseline_kgco2 - actual_kgco2`.

## [CALC-02] Supply Mix Integrity
- **Logic**: `local_renewables_mwh` = `solar.used_directly_mwh` + (Battery Discharge if the battery was previously charged via solar).
- **Effective RE %**: `((local_renewables_mwh + (grid_import_mwh * grid_metrics.renewable_percentage / 100)) / total_load) * 100`.

## [CALC-03] Solar Balancing
- **Balance Equation**: `actual_solar_mwh` = `solar.used_directly_mwh` + `solar.stored_mwh` + `solar.curtailed_mwh`. 
- **Validation**: Curtailed energy must be reported if `stored_mwh` and `used_directly_mwh` cannot account for 100% of generation.