# INCIDENT RESPONSE AND FALLBACK REASONING

## FALLBACK-01: Missing or Empty Forecast Data

### Scenario
- forecast_context.data is empty, null, or contains fewer than 3 entries.
- OR forecast_context key is missing entirely from telemetry.

### Action
- Select SVC_SAFE_THROTTLE immediately.
- Do NOT attempt to guess solar or load values.

### Reasoning Template
"Forecast data unavailable or incomplete. Reverting to SVC_SAFE_THROTTLE to prevent uncontrolled battery depletion."

---

## FALLBACK-02: Solar Over-Generation (Unforecasted Surplus)

### Scenario
- actual_solar_mwh is significantly HIGHER than forecast_solar_mwh (e.g., actual > 1.5× forecast for T+0).
- This means the solar model underestimated generation.

### Action
- Prioritize SVC_MAX_RENEWABLE to capture the unexpected surplus.
- Charge battery immediately before the surplus dissipates.

### Reasoning Template
"Unforecasted solar surplus detected (actual: X MWh vs forecast: Y MWh). Switching to SVC_MAX_RENEWABLE to store excess energy and prevent grid over-voltage."

---

## FALLBACK-03: Low SOC During High Carbon Window

### Scenario
- soc_percent drops below 18% during a period when carbon_intensity > 600.
- The agent might be tempted to keep discharging to save carbon.

### Action
- STOP discharge immediately, even if saved_kgco2 would be high.
- Switch to IDLE or CHARGE from grid if carbon_intensity < 500.
- Switch to SVC_SAFE_THROTTLE if carbon_intensity > 500 (do not charge from dirty grid).

### Reasoning Template
"Critical SOC boundary (20%) approached. Grid import resumed to preserve battery health despite high carbon intensity of X gCO2/kWh."

---

## FALLBACK-04: Telemetry Mismatch (Sensor Error)

### Scenario
- actual_load_mwh is negative (impossible for load).
- OR actual_solar_mwh is negative.
- OR battery.soc_percent > 100 or < 0.

### Action
- SVC_SAFE_THROTTLE immediately.
- Flag as sensor error.

### Reasoning Template
"Telemetry contains physically impossible values (load: X, solar: Y, SOC: Z%). Sensor error suspected. Engaging safe throttle."

---

## FALLBACK-05: Rapid Demand Ramp (Grid Shock)

### Scenario
- Ramp Rate (change in demand) exceeds 500 MW/hr based on load data patterns.
- OR actual_load increases by more than 30% compared to the previous dispatch cycle.

### Action
- If SOC > 40%: Switch to SVC_PEAK_SHAVING immediately.
- If SOC < 40%: Switch to SVC_SAFE_THROTTLE (cannot safely discharge).

### Reasoning Template
"Rapid demand ramp detected (rate: X MW/hr). Battery SOC at Y%. Engaging SVC_PEAK_SHAVING to buffer grid stress."