# H-ENERGY STRATEGIC DISPATCH LOGIC & SAFETY SAFETY PROCEDURES

This document defines the mathematical logic, safety constraints, and decision matrix for selecting the optimal Energy Service (SVC) strategy. The AI Agent must cross-reference telemetry against these rules before final selection.

---

## 1. THE FOUR CORE STRATEGIES (MATHEMATICAL DEFINITIONS)

### 1.1 SVC_MAX_RENEWABLE (Surplus Management)
*   **Intent**: Maximize self-consumption of local solar generation. Zero export to grid unless battery is full.
*   **Mathematical Trigger**:
    $$ \text{Net Demand} = \text{Forecast Load} - \text{Forecast Solar} $$
    *   **Condition**: `Net Demand < 0` (Negative Net Demand) for > 50% of the next 6 prediction steps.
    *   **Secondary Indicator**: `solar_roll3h` (3-hr rolling avg) is rising, indicating sustained solar ramp-up.
*   **Execution Logic** (Matches `svc_max_renewable.py`):
    1.  Calculated `Surplus MWh` = `max(0, solar - load)`.
    2.  Check Battery Headroom: `Capacity - Current Energy`.
    3.  `stored_mwh` = `min(surplus_solar, room_in_battery, 2.0)` (Clamped by 2.0 MWh Max Charge Rate).
    4.  If `surplus > stored`: Curtail excess.

### 1.2 SVC_PEAK_SHAVING (Grid Stress Mitigation)
*   **Intent**: Discharge battery to flatten grid demand spikes, preventing high carbon imports.
*   **Mathematical Trigger**:
    *   **Ramp Condition**: `Forecast Load(t+3)` > `Forecast Load(t)` * 1.25 (25% increase over 3 hours).
    *   **OR Absolute Peak**: `Forecast Load` > 80th Percentile of `Demand_MWh` profile (>4000 MWh based on analysis).
*   **Safety Constraints**:
    *   `SoC_Percent` must be > 40% to initiate.
    *   Discharge must stop if `SoC` hits 20% (Soft Floor).
*   **Execution Logic** (Matches `svc_peak_shaving.py`):
    1.  `usable_energy` = `max(0, current_energy - (capacity * 0.20))` (Preserves 20% Buffer).
    2.  `discharged` = `min(load_gap, usable_energy, 2.5)` (Clamped by 2.5 MWh Max Discharge Rate).

### 1.3 SVC_LOW_CARBON_GRID (Strategic Arb)
*   **Intent**: Pre-charge battery during low-carbon grid hours to use during dirty peaks (e.g., night pre-charging).
*   **Mathematical Trigger**:
    *   **Solar condition**: `actual_solar_mwh` ≈ 0 (Night/Low Light).
    *   **Carbon Condition**: `grid_metrics.carbon_intensity` < 500 gCO2/kWh.
    *   **SoC Condition**: `SoC_Percent` < 60%.
*   **Execution Logic** (Matches `svc_low_carbon_grid.py`):
    1.  `target_energy` = `capacity * 0.70` (Target 70% Charge).
    2.  `charge_needed` = `max(0, target_energy - current_energy)`.
    3.  `charge_amount` = `min(charge_needed, 2.0)` (Clamped by 2.0 MWh Max Charge Rate).
    4.  Charge comes from Grid (since Solar is ~0).

### 1.4 SVC_SAFE_THROTTLE (Fallback Protection)
*   **Intent**: Stabilize system, disconnect heavy loads, or stop discharging during uncertainty.
*   **Mathematical Trigger (ANY of below)**:
    *   **Critical Low SoC**: `SoC_Percent` < 15% (Hard Floor).
    *   **Telemetry Deviation**: `|Actual Load - Forecast Load|` > 50% Error.
    *   **Missing Data**: `Forecast Context` is empty or null.
*   **Execution Logic**:
    1.  Set Battery Mode: `IDLE` (No Charge/Discharge).
    2.  Flag Alert: "Telemetry anomaly or Safety Floor breach."

---

## 2. OPERATIONAL SAFETY PROCEDURES (HARD LIMITS)

The Agent must **NEVER** violate these physics constraints, regardless of strategy:

### 2.1 Battery State of Charge (SoC) Boundaries
| Zone | Range | Action Allowed |
| :--- | :--- | :--- |
| **Deep Discharge Risk** | 0% - 15% | **STOP**. Force IDLE/CHARGE. No Discharge. |
| **Strategic Reserve** | 15% - 20% | Discharge only for Critical Loads (not Grid Arb). |
| **Operational Band** | 20% - 95% | Free Operation for all Strategies. |
| **Overcharge Risk** | 95% - 100% | **STOP CHARGE**. Force Discharge or IDLE. |

### 2.2 C-Rate Limits (Power Constraints)
*   **Max Charge MWh/30min**: 2.0 MWh
*   **Max Discharge MWh/30min**: 2.5 MWh
*   *Math:* If `Requested Strategy Delta` > Limit, clamp value to Limit.

---

## 3. DATA PROFILE UTILIZATION RULES

Use these features from the data profiles to refine decisions:

### 3.1 Analyzing Solar Data (`HOURLY_SOLAR_DATA`)
*   **Lag Features (`solar_lag_1h`)**: Use to validate if forecast is hallucinating. If `solar_lag_1h` was 0 and `forecast` is 500 MWh (at 6 AM), trust the forecast (sunrise). If `solar_lag_1h` was 500 and forecast is 0 (at noon), assume Cloud Cover -> Trigger `SVC_SAFE_THROTTLE`.
*   **Rolling Mean (`solar_roll3h`)**: Use to smooth erratic telemetry. Do not switch strategies based on a single spike; wait for the rolling mean to shift.

### 3.2 Analyzing Load Data (`haryana_hourly_generation`)
*   **Ramp Rate (`Ramp Rate`)**:
    *   If `Ramp Rate` > 500 MW/hr: This is a **Grid Shock**. Immediately switch to `SVC_PEAK_SHAVING` if SoC permits.
    *   If `Ramp Rate` is negative: Load is shedding. Consider `SVC_MAX_RENEWABLE` (Charging) if solar is active.
*   **Carbon Intensity Proxies**:
    *   The load file contains `Coal_Gas`. If `Coal_Gas` ratio in the mix is increasing, `Carbon Intensity` is rising. Prioritize **Carbon-Aware** logic.

---

## 4. FINAL SELECTION MATRIX

| Net Demand | SoC | Carbon | Solar | **STRATEGY** |
| :--- | :--- | :--- | :--- | :--- |
| Negative | < 95% | Any | High | **SVC_MAX_RENEWABLE** |
| Positive (High) | > 40% | High (>600) | Low | **SVC_PEAK_SHAVING** |
| Positive | < 60% | Low (<500) | Zero | **SVC_LOW_CARBON_GRID** |
| Any | < 15% | Any | Any | **SVC_SAFE_THROTTLE** |
| Unknown | Any | Any | Any | **SVC_SAFE_THROTTLE** |

---

## 5. REGIONAL OVERRIDES (HARYANA / IN-NO)

Apply these rules strictly when `Region="Haryana"`:

### 5.1 The "7 PM Rule" (Peak Shaving Priority)
*   **Trigger**: Hour is 19:00 (7 PM).
*   **Action**: If `SoC` > 50%, FORCE `SVC_PEAK_SHAVING` regardless of Load Forecast delta.
*   **Reasoning**: Pre-emptive strike against the known nightly carbon spike in Northern India.

### 5.2 The "Fog Protocol" (Winter Reliability)
*   **Trigger**: Month is Dec/Jan AND `forecast_solar` > 100 AND `actual_solar` < 10 (High Prediction, Low Reality).
*   **Action**: Switch to `SVC_SAFE_THROTTLE`.
*   **Reasoning**: Likely heavy smog/fog event common in NCR. Forecasts are unreliable.

### 5.3 Sunday Surplus
*   **Trigger**: `Weekday` is Sunday (Index 6) AND `Net Demand` is locally positive but low.
*   **Action**: Bias towards `SVC_MAX_RENEWABLE` (Charge).
*   **Reasoning**: Industrial load is off; grid is likely spilling renewables. Absorb it.
