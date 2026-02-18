# REGIONAL CONTEXT: NORTHERN INDIA (IN-NO) — HARYANA/NCR

## GRID CHARACTERISTICS

### Region
- SLDC: Haryana State Load Despatch Centre
- Region Code: IN-NO (Northern Regional Load Despatch Centre)
- Dominant Load: Mixed Industrial (Manesar/Gurugram corridor) and Agricultural (tubewell pumping)

### Grid Stability
- Evening frequency drops are common during the 18:00-19:00 solar-to-coal-transition.
- The agent should anticipate this transition and pre-position battery state accordingly.

## SEASONAL DEMAND PATTERNS

### Summer (April - September)
- Solar Window: 06:00 - 18:30 (Peak generation at 13:00)
- Night Peak: 20:00 - 23:59 (AC/cooling load, highest priority for discharge)
- Day Peak: 14:00 - 16:00 (Industrial + cooling overlap)
- Carbon: Highest at night when coal peaking plants activate

### Winter (October - March)
- Solar Window: 07:30 - 16:30 (shortened by 2+ hours)
- Evening Peak: 18:00 - 21:00 (lighting + heating load)
- Morning Peak: 07:00 - 09:00 (geysers + space heating)
- Fog Impact: Expect 50-80% solar output reduction in December-January mornings
- Agent must NOT trust solar forecasts during fog events

### Monsoon (July - September)
- Cloud cover reduces solar output by 30-60% vs clear-sky baseline
- solar_roll3h feature from LGBM model becomes critical for real-time adjustment
- Bias toward SVC_SAFE_THROTTLE during heavy rain events

## CARBON INTENSITY PATTERNS (HARYANA)

### Peak Carbon Hours: 19:00 - 23:00
- Carbon intensity typically exceeds 750 gCO2/kWh
- Coal-based peaking plants are activated to cover evening demand
- Agent should NEVER charge from grid during these hours
- Agent should ALWAYS discharge if SOC > 40%

### Clean Grid Hours: 02:00 - 06:00
- Carbon intensity drops below 400 gCO2/kWh
- Nuclear and hydro baseload dominates
- Best window for SVC_LOW_CARBON_GRID (grid pre-charging)

### Solar Hours: 09:00 - 16:00
- Mixed carbon (400-600 gCO2/kWh) due to solar contribution
- Agent should prioritize SVC_MAX_RENEWABLE during these hours

## TIME-OF-DAY AGENT RULES

### The 7 PM Rule
- If current hour >= 19:00 AND SOC > 50%: Force SVC_PEAK_SHAVING.
- Reasoning: Pre-emptive strike against the known nightly coal spike.

### The Fog Protocol (Winter)
- If Month is December or January AND forecast solar > 100 MWh AND actual solar < 10 MWh:
- Conclusion: Dense fog/smog event. Switch to SVC_SAFE_THROTTLE.
- Do NOT trust the solar forecast model during these conditions.

### Sunday Surplus
- Industrial load drops ~20% on Sundays (Weekday index 6).
- Grid is likely spilling excess renewables.
- Bias toward SVC_MAX_RENEWABLE to absorb the surplus.

### Tariff Logic
- The agent should treat "High Carbon Intensity" as a proxy for "High Cost."
- This aligns carbon optimization with economic optimization for the grid operator.
- Charging during clean/cheap hours (02:00-06:00) and discharging during dirty/expensive hours (19:00-23:00) maximizes both carbon savings and economic value.

## DEMAND RAMP CHARACTERISTICS

### Evening Ramp (Critical)
- The Haryana grid experiences sharp ramps of ~500 MW/hr around 18:00.
- This is caused by: Solar fade + lighting load + returning commuters.
- Agent should reserve at least 30% SOC for the 18:00-19:00 transition.

### Morning Ramp (Moderate)  
- Demand increases 200-300 MW/hr between 06:00-08:00.
- Less critical but coincides with solar ramp-up.
- Agent can usually handle this with SVC_MAX_RENEWABLE.

### Weekend vs Weekday
- Weekday demand is ~20% higher than weekend demand.
- Peak hours shift slightly on weekends (later evening peak around 21:00).