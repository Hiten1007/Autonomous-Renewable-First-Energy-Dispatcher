# INCIDENT RESPONSE AND FALLBACK REASONING
## [FALLBACK-01] Missing Forecast Data
- **Scenario**: `forecast_context` data is empty or corrupted.
- **Action**: Trigger `SVC_SAFE_THROTTLE`.
- **Reasoning**: "Forecast data unavailable; reverting to safe throttle to prevent uncontrolled battery depletion."

## [FALLBACK-02] Telemetry Discrepancy
- **Scenario**: `actual_solar_mwh` is significantly higher than `forecast_solar_mwh` (Over-generation).
- **Action**: Prioritize `SVC_MAX_RENEWABLE`. 
- **Reasoning**: "Unforecasted solar surplus detected. Diverting to BESS storage to prevent grid over-voltage."

## [FALLBACK-03] Low SoC Stress
- **Scenario**: `soc_percent` drops below 18% during a High Carbon window.
- **Action**: Discontinue discharge even if `saved_kgco2` is high. 
- **Reasoning**: "Critical SoC boundary (20%) approached. Grid import resumed to preserve battery health despite high carbon intensity."