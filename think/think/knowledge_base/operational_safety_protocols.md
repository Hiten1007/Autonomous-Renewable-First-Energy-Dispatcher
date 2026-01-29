# SAFETY AND OPERATIONAL BOUNDARIES
## [BESS-01] Battery State of Charge (SoC) Limits
- **Hard Floor**: 15% SoC. Below this, `battery.state` must be IDLE or CHARGE.
- **Soft Floor**: 20% SoC. This is the "Strategic Reserve." No discharge permitted unless `grid_metrics.renewable_percentage` < 5%.
- **Ceiling**: 98% SoC. Stop `stored_mwh` to prevent cell degradation.

## [LIMIT-01] Power Transfer Rates (C-Rate)
- **Max Discharge Rate**: 2.5 MWh per 30-minute window (5MW peak).
- **Max Charge Rate**: 2.0 MWh per 30-minute window.
- **Logic**: If the agent calculates a `battery.delta_mwh` exceeding these, it must curtail solar or import from grid to fill the gap.

## [ENV-01] Thermal and Contextual Safety
- **High Demand Hours**: 18:00 - 22:00. During these hours, avoid `SVC_MAX_RENEWABLE` export; preserve battery for internal load coverage.