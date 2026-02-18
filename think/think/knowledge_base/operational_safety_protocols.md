# OPERATIONAL SAFETY PROTOCOLS — H-ENERGY GRID MANAGEMENT

## BATTERY STATE OF CHARGE (SOC) LIMITS

### Hard Floor: 15% SOC
- Below 15% SOC, the battery MUST be set to IDLE or CHARGE.
- No discharge is permitted under any circumstance.
- The agent must select SVC_SAFE_THROTTLE immediately.
- Reasoning: Prevents deep discharge damage to lithium-ion cells.

### Soft Floor: 20% SOC (Strategic Reserve)
- Between 15-20% SOC, discharge is only permitted if grid_metrics.renewable_percentage < 5%.
- This reserve exists for emergency grid blackout scenarios.
- Under normal conditions: Stop discharge at 20%.

### Ceiling: 98% SOC
- Above 98% SOC, stop all charging immediately.
- Set battery mode to IDLE or DISCHARGE.
- Reasoning: Prevents thermal runaway and cell degradation from overcharging.

### Operational Band: 20% - 95% SOC
- All four strategies (SVC_MAX_RENEWABLE, SVC_PEAK_SHAVING, SVC_LOW_CARBON_GRID, SVC_SAFE_THROTTLE) may operate freely within this band.

## POWER TRANSFER RATE LIMITS (C-RATE)

### Maximum Charge Rate
- 2.0 MWh per 30-minute control window.
- If solar surplus exceeds 2.0 MWh, excess must be curtailed.

### Maximum Discharge Rate
- 2.5 MWh per 30-minute control window.
- If load gap exceeds 2.5 MWh, grid import must cover the difference.

### Enforcement
- If the agent calculates a battery delta_mwh exceeding these limits, clamp the value to the limit.
- Never exceed C-rate limits even during emergencies.

## HIGH DEMAND HOURS (HARYANA)

### Evening Peak: 18:00 - 22:00
- During these hours, avoid using SVC_MAX_RENEWABLE for export.
- Preserve battery capacity for internal load coverage.
- Prioritize SVC_PEAK_SHAVING if SOC > 40%.

### Morning Peak: 07:00 - 09:00 (Winter Only)
- Heating load spikes in December/January.
- Reserve 30% SOC for this period if forecast shows high demand.

## THERMAL AND ENVIRONMENTAL SAFETY

### Fog Protocol (December/January)
- When Month is December or January AND forecast_solar_mwh > 100 AND actual_solar_mwh < 10:
- Conclusion: Dense fog/smog event. Solar forecast is unreliable.
- Action: Switch to SVC_SAFE_THROTTLE until solar actuals match forecasts.

### Grid Frequency Events
- If actual_load_mwh > 1.5x forecast_load_mwh:
- Conclusion: Grid frequency disturbance or sudden demand spike.
- Action: SVC_SAFE_THROTTLE to prevent uncontrolled battery depletion.