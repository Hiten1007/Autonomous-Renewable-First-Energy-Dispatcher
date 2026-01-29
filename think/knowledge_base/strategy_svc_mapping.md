# ENERGY STRATEGY TO SVC MAPPING
## [SVC_MAX_RENEWABLE] - Local Green Priority
- **Trigger Pattern**: `forecast_context.data` shows negative `net_demand_mwh` for >50% of the 6-hour window.
- **Priority**: Primary.
- **Goal**: Zero `curtailed_mwh`. 
- **Operational Logic**: If `soc_percent` < 90%, prioritize `stored_mwh`. If `soc_percent` > 90%, prioritize `used_directly_mwh` and only then export/curtail.

## [SVC_PEAK_SHAVING] - Demand Stress Management
- **Trigger Pattern**: `forecast_load_mwh` shows a delta increase of >25% between T+0 and T+3.
- **Priority**: High (if grid carbon is high).
- **Goal**: Minimize `grid_import_mwh` during the peak hour.
- **Operational Logic**: Calculate `battery.delta_mwh` to ensure `soc_after_mwh` does not hit the 20% floor before the peak ends.

## [SVC_LOW_CARBON_GRID] - Strategic Grid Mix
- **Trigger Pattern**: `actual_solar_mwh` is 0 (night) AND `grid_metrics.carbon_intensity_direct_gco2_per_kwh` < 500.
- **Priority**: Moderate.
- **Goal**: Pre-charge battery during "Clean Grid" hours to prepare for "Dirty Grid" peaks.
- **Operational Logic**: Charge battery from grid imports only up to 70% SoC to leave room for morning solar.

## [SVC_SAFE_THROTTLE] - System Protection
- **Trigger Pattern**: `actual_load_mwh` > 1.5x `forecast_load_mwh` OR `soc_percent` < 15%.
- **Priority**: Mandatory/Override.
- **Goal**: Maintain grid connection without discharging.