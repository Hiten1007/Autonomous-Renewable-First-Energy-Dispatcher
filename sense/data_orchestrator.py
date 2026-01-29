import json
from datetime import datetime

# ---- IMPORT DATA SOURCES ----
from real_values import get_current_actuals
from get_battery_state import get_battery_state
from grid_carbon_info import get_grid_metrics
from load_predictor import get_load_forecast
from live_predictor import get_solar_forecast


REGION = "IN-NO"
FORECAST_HORIZON = 6


def build_llm_context(trigger_time: datetime):
    # 1️⃣ Actual 30-min values
    actuals = get_current_actuals(trigger_time)
    # expected:
    # { "solar_mwh": float, "load_mwh": float }

    # 2️⃣ Battery state
    battery = get_battery_state()
    # expected:
    # { "energy_mwh": float, "capacity_mwh": float, "soc_percent": float }

    # 3️⃣ Grid metrics
    grid = get_grid_metrics(region=REGION)
    # expected:
    # { "carbon_intensity": int, "re_percent": int, "cfe_percent": int }

    # 4️⃣ Forecasts (hourly)
    solar_fc = get_solar_forecast(trigger_time, hours=FORECAST_HORIZON)
    load_fc = get_load_forecast(trigger_time, hours=FORECAST_HORIZON)

    forecast_data = []
    for h in range(1, FORECAST_HORIZON + 1):
        solar = solar_fc[h]
        load = load_fc[h]
        forecast_data.append({
            "t_plus_hours": h,
            "forecast_solar_mwh": round(solar, 2),
            "forecast_load_mwh": round(load, 2),
            "net_demand_mwh": round(load - solar, 2)
        })

    # 5️⃣ Assemble FINAL context
    context = {
        "metadata": {
            "trigger_timestamp": trigger_time.isoformat(),
            "region": REGION
        },

        "current_state": {
            "resolution": "30min",
            "actual_solar_mwh": round(actuals["solar_mwh"], 2),
            "actual_load_mwh": round(actuals["load_mwh"], 2),
            "battery": battery
        },

        "grid_metrics": {
            "carbon_intensity_direct_gco2_per_kwh": grid["carbon_intensity_direct_gco2_per_kwh"],
            "carbon_intensity_lifecycle_gco2_per_kwh" : grid["carbon_intensity_lifecycle_gco2_per_kwh"],
            "renewable_percentage": grid["renewable_percentage"],
            "carbon_free_percentage": grid["carbon_free_percentage"]
        },

        "forecast_context": {
            "resolution": "hourly",
            "note": (
                "All forecast values represent total energy over one full hour. "
                "The control step is 30 minutes. Forecasts are provided for planning context only."
            ),
            "horizon_hours": FORECAST_HORIZON,
            "data": forecast_data
        }
    }

    return context


# ---- RUNNER (30-MIN LOOP SAFE) ----
if __name__ == "__main__":
    now = datetime.now()

    context = build_llm_context(now)

    print("\n===== LLM INPUT CONTEXT =====\n")
    print(json.dumps(context, indent=2))
