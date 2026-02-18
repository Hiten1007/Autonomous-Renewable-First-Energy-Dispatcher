# HARYANA (INDIA) REGIONAL ENERGY PROFILE

## 1. GRID CHARACTERISTICS
*   **Region Code**: IN-NO (Northern Regional Load Despatch Centre).
*   **Dominant Load Type**: Mixed Industrial (Manesar/Gurugram) and Agricultural (Tubewells).
*   **Critical Constraint**: "Evening Peak" driven by lighting + residential AC (Summer) or heating (Winter).

## 2. SEASONAL PATTERNS (Time of Use)

### 2.1 SUMMER (Apr - Sep)
*   **Solar Window**: 06:00 - 18:30 (Peak @ 13:00).
*   **Peak Demand Hours**: 
    *   **Night Peak**: 20:00 - 23:59 (AC Load). *Highest Priority for Battery Discharge.*
    *   **Day Peak**: 14:00 - 16:00 (Industrial + cooling).
*   **Carbon Intensity**: High at night (Coal base load).

### 2.2 WINTER (Oct - Mar)
*   **Solar Window**: 07:30 - 16:30 (Shortened).
*   **Peak Demand Hours**: 
    *   **Evening Peak**: 18:00 - 21:00 (Lighting + Heating).
    *   **Morning Peak**: 07:00 - 09:00 (Geysers/Heating).
*   **Fog Impact**: Expect 80% solar drop during Jan/Dec mornings due to dense fog/smog.

## 3. SPECIFIC DATA TRIGGERS
*   **Ramp Events**: Haryana grid experiences sharp ramps (~500 MW/hr) around 18:00 when solar fades and lighting load kicks in.
    *   *Agent Action*: Reserve 30% SOC for 18:00-19:00 transition.
*   **Coal Dependency**: 
    *   Hours 19:00-04:00 are almost exclusively Coal-powered (~850 gCO2/kWh).
    *   *Agent Action*: `SVC_LOW_CARBON_GRID` (Grid Charging) should ONLY occur between 04:00-06:00 or 12:00-15:00.

## 4. AGENT RULES OF THUMB
1.  **"The 7 PM Rule"**: If SOC > 50% at 19:00, DISCHARGE Aggressively (`SVC_PEAK_SHAVING`).
2.  **"The Fog Protocol"**: In January, if forecast solar is high but `solar_lag_1h` is 0, assume Fog. Throttle expectations.
3.  **"Weekend Drop"**: Industrial load drops ~20% on Sundays. Prioritize `SVC_MAX_RENEWABLE` (Charging) on Sundays to absorb surplus.
