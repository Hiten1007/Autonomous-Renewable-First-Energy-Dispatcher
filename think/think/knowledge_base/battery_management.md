# BATTERY MANAGEMENT AND LIFECYCLE PROTOCOLS

## BATTERY SPECIFICATION (BESS)

### Capacity
- Total capacity: 5200 MWh (based on current system configuration)
- Usable capacity: 4160 MWh (between 20% and 100% SOC)
- Strategic reserve: 780 MWh (15-20% SOC, emergency only)

### State Definitions
- CHARGE: Battery is actively receiving energy (from solar or grid)
- DISCHARGE: Battery is actively supplying energy to the load
- IDLE: No energy flow. Battery maintains current state.
- STANDBY: Same as IDLE (used by SVC_SAFE_THROTTLE)

## STRATEGY-TO-BATTERY-INTENT MAPPING

### SVC_MAX_RENEWABLE → Battery Intent
- mode: CHARGE
- priority: SOLAR_ONLY (only charge from surplus solar, never from grid)
- target_soc_percent: 90 (leave 10% headroom for safety)
- max_c_rate: NORMAL (≤ 2.0 MWh per 30-min window)

### SVC_PEAK_SHAVING → Battery Intent
- mode: DISCHARGE
- priority: NONE (discharge to cover load gap)
- target_soc_percent: 20 (stop at soft floor)
- max_c_rate: HIGH (≤ 2.5 MWh per 30-min window)

### SVC_LOW_CARBON_GRID → Battery Intent
- mode: CHARGE
- priority: GRID_ALLOWED (charge from the grid since solar is unavailable)
- target_soc_percent: 70 (leave 30% headroom for morning solar ramp)
- max_c_rate: NORMAL (≤ 2.0 MWh per 30-min window)

### SVC_SAFE_THROTTLE → Battery Intent
- mode: IDLE
- priority: NONE
- target_soc_percent: (maintain current SOC, no change)
- max_c_rate: NONE (zero energy flow)

## SOC MANAGEMENT BEST PRACTICES

### Pre-Peak Positioning
- By 17:00, battery SOC should ideally be > 60%.
- This ensures enough energy for the 19:00-23:00 Haryana evening peak.
- If SOC < 40% at 17:00 AND carbon < 500, consider emergency SVC_LOW_CARBON_GRID.

### Post-Peak Recovery
- After 23:00, if SOC < 30%, initiate SVC_LOW_CARBON_GRID during 02:00-06:00 clean window.
- Goal: Recover to at least 50% SOC before the next day's solar ramp-up.

### Solar Day Planning
- During peak solar hours (09:00-15:00), maintain SVC_MAX_RENEWABLE to fill battery.
- By 15:00, battery should be approaching 80-90% SOC for evening discharge.

## DEGRADATION AWARENESS

### Cycle Counting
- Each full charge-discharge cycle reduces battery lifespan.
- Shallow cycles (30-70% SOC) are preferred over deep cycles (15-95%).
- The agent should avoid unnecessarily deep discharges when shallow discharge can meet the load gap.

### Temperature Considerations
- In Haryana summers (May-June), ambient temperatures exceed 45°C.
- High temperature accelerates degradation. Limit discharge to 2.0 MWh during extreme heat.
- The agent does not currently receive temperature telemetry but should bias toward conservative operation in summer months.
