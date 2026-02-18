# STRATEGY TO SERVICE MAPPING — ENERGY DISPATCH

## SVC_MAX_RENEWABLE — Local Green Priority

### When to Use
- Trigger: More than 50% of forecast_context.data entries show negative net_demand_mwh (solar surplus).
- Secondary: solar rolling 3-hour average is rising, indicating sustained generation.
- Confirm: SOC is below 95% (room to charge).

### Goal
- Zero curtailed_mwh. Every watt of solar should be used or stored.

### Operational Logic (Matches svc_max_renewable.py)
1. used_directly_mwh = min(solar, load)
2. surplus_solar = max(0, solar - load)
3. room_in_battery = capacity - current_energy
4. stored_mwh = min(surplus_solar, room_in_battery, 2.0) — Max charge rate is 2.0 MWh
5. curtailed_mwh = surplus_solar - stored_mwh
6. grid_import = max(0, load - used_directly)

### Battery Intent
- mode: CHARGE
- priority: SOLAR_ONLY
- target_soc_percent: 90
- max_c_rate: NORMAL

---

## SVC_PEAK_SHAVING — Demand Stress Management

### When to Use
- Trigger: forecast_load_mwh increases >25% between T+0 and T+3.
- OR: Hour is 19:00+ in Haryana AND SOC > 50% (The 7 PM Rule).
- OR: forecast_load_mwh exceeds 4000 MWh (80th percentile for Haryana).
- Confirm: SOC > 40%.

### Goal
- Minimize grid_import_mwh during the peak hour.

### Operational Logic (Matches svc_peak_shaving.py)
1. used_directly = min(solar, load)
2. load_gap = load - used_directly
3. usable_energy = max(0, current_energy - (capacity × 0.20)) — Preserves 20% SOC buffer
4. discharged = min(load_gap, usable_energy, 2.5) — Max discharge rate is 2.5 MWh
5. grid_import = load_gap - discharged

### Battery Intent
- mode: DISCHARGE
- priority: NONE
- target_soc_percent: 20 (floor)
- max_c_rate: HIGH

---

## SVC_LOW_CARBON_GRID — Strategic Grid Charging

### When to Use
- Trigger: actual_solar_mwh ≈ 0 (nighttime) AND carbon_intensity_direct_gco2_per_kwh < 500.
- Confirm: SOC < 60%.
- Best hours: 02:00 - 06:00 when grid is cleanest (nuclear/hydro baseload).

### Goal
- Pre-charge battery during clean grid hours to use during dirty coal peaks later.

### Operational Logic (Matches svc_low_carbon_grid.py)
1. target_energy = capacity × 0.70 — Target 70% SOC (leave room for morning solar)
2. charge_needed = max(0, target_energy - current_energy)
3. charge_amount = min(charge_needed, 2.0) — Max charge rate is 2.0 MWh
4. grid_import = (load - used_directly) + charge_amount

### Battery Intent
- mode: CHARGE
- priority: GRID_ALLOWED
- target_soc_percent: 70
- max_c_rate: NORMAL

---

## SVC_SAFE_THROTTLE — System Protection Fallback

### When to Use
- Trigger (ANY of these):
  - SOC < 15% (Hard Floor breach)
  - actual_load_mwh > 1.5× forecast_load_mwh (Telemetry discrepancy)
  - forecast_context is empty, null, or corrupted
  - Month is Dec/Jan AND forecast solar is high but actual solar is near zero (Fog Protocol)

### Goal
- Maintain grid connection without battery activity. Protect the system.

### Operational Logic (Matches svc_safe_throttle.py)
1. used_directly = min(solar, load)
2. grid_import = load - used_directly
3. Battery delta = 0 (no charge, no discharge)

### Battery Intent
- mode: IDLE
- priority: NONE
- target_soc_percent: (current, no change)
- max_c_rate: NONE