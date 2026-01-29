# REGIONAL CONTEXT: NORTHERN INDIA (IN-NO)
## [REGION-CONTEXT] Haryana/NCR Grid Characteristics
- **Peak Carbon Hours**: Typically 19:00 to 23:00 when coal-based peaking plants are active. Carbon intensity often exceeds 750 gCO2/kWh.
- **Solar Windows**: 09:00 to 16:30. High variability in Gurugram/Hisar regions due to dust/aerosols.
- **Grid Stability**: Frequency drops are common during evening transitions.
- **Decision Advice**: If current time is 17:00, use `SVC_PEAK_SHAVING` immediately to prepare for the 19:00 coal-peak, even if load is currently low.

## [TARIFF-LOGIC] Time-of-Day (ToD) Strategies
- The agent should treat "High Carbon Intensity" as a proxy for "High Cost" to align with grid economic incentives.