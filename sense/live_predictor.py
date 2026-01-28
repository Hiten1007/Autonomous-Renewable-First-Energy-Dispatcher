import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
API_KEY = "H74KXGYYCRYWG9E7Y478K8CC3"
LOCATIONS = ["Panchkula,IN", "Rohtak,IN", "Gurugram,IN", "Hisar,IN", "Yamunanagar,IN"]
AVG_LAT = 29.0
AVG_LON = 76.0

MODEL_PATH = "solar_forecast_model.pkl"
SCALER_PATH = "scaler.pkl"

MAX_SOLAR_MWh = 4000
KT_ATTENUATION = 0.75

# Load model and scaler once globally for efficiency
MODEL = joblib.load(MODEL_PATH)
SCALER = joblib.load(SCALER_PATH)

def fetch_live_weather_history():
    """Fetches historical weather to calculate lags and features."""
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{','.join(LOCATIONS)}/last24hours"
    params = {"unitGroup": "metric", "include": "hours", "key": API_KEY, "contentType": "json"}
    
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    rows = []
    for day in data["days"]:
        for h in day["hours"]:
            dt = datetime.fromisoformat(f"{day['datetime']}T{h['datetime']}")
            cloud = h.get("cloudcover", 0)
            temp = h.get("temp", 25)
            wind = h.get("windspeed", 2)
            kt = np.clip(1 - (cloud / 100) * KT_ATTENUATION, 0.05, 0.85)
            rows.append({
                "datetime": dt,
                "ALLSKY_KT_HOURLY": kt,
                "T2M_HOURLY": temp,
                "WS10M_HOURLY": wind
            })
    return pd.DataFrame(rows).set_index("datetime").sort_index()

def estimate_solar(weather_hist):
    """Virtual sensor to create historical solar data for lags."""
    records = []
    for dt, row in weather_hist.iterrows():
        hour = dt.hour
        daily_cycle = np.sin((hour - 6) * np.pi / 12) if 6 <= hour <= 18 else 0
        solar = MAX_SOLAR_MWh * daily_cycle * row["ALLSKY_KT_HOURLY"]
        records.append({"datetime": dt, "solar_mwh": max(0, solar)})
    return pd.DataFrame(records).set_index("datetime")

def create_feature_vector(t, solar_hist, weather_hist):
    """Creates the single row input vector for the multi-output model."""
    hour_sin = np.sin(2 * np.pi * t.hour / 24)
    hour_cos = np.cos(2 * np.pi * t.hour / 24)
    month_sin = np.sin(2 * np.pi * t.month / 12)
    month_cos = np.cos(2 * np.pi * t.month / 12)
    is_day = 1 if 6 <= t.hour <= 18 else 0

    def lag(h):
        try: return solar_hist.asof(t - timedelta(hours=h))["solar_mwh"]
        except: return 0

    solar_lag_1h  = lag(1)
    solar_lag_3h  = lag(3)
    solar_lag_6h  = lag(6)
    solar_lag_24h = lag(24)

    end = t - timedelta(seconds=1)
    solar_roll3h  = solar_hist.loc[end - timedelta(hours=3):end]["solar_mwh"].mean()
    solar_roll24h = solar_hist.loc[end - timedelta(hours=24):end]["solar_mwh"].mean()

    wx = weather_hist.asof(t)
    kt = wx["ALLSKY_KT_HOURLY"] if is_day else 0.0
    temp = wx["T2M_HOURLY"]
    wind = wx["WS10M_HOURLY"]

    df_feat = pd.DataFrame({
        "hour_sin": [hour_sin], "hour_cos": [hour_cos],
        "month_sin": [month_sin], "month_cos": [month_cos],
        "LAT": [AVG_LAT], "LON": [AVG_LON], "is_day": [is_day],
        "solar_lag_1h": [solar_lag_1h], "solar_lag_3h": [solar_lag_3h],
        "solar_lag_6h": [solar_lag_6h], "solar_lag_24h": [solar_lag_24h],
        "solar_roll3h": [solar_roll3h], "solar_roll24h": [solar_roll24h],
        "ALLSKY_KT_HOURLY": [kt], "T2M_HOURLY": [temp], "WS10M_HOURLY": [wind],
    })
    
    # Apply scaling
    df_feat[["LAT", "LON"]] = SCALER.transform(df_feat[["LAT", "LON"]])
    return df_feat

# -------- NEW ORCHESTRATOR COMPATIBLE FUNCTION --------
def get_solar_forecast(trigger_time, hours=6):
    """
    Produces a dictionary where keys are 1 to 'hours' and values are MWh.
    e.g. {1: 150.2, 2: 340.5, ...}
    """
    weather_hist = fetch_live_weather_history()
    solar_hist = estimate_solar(weather_hist)
    
    # Prepare input for the model
    X = create_feature_vector(trigger_time, solar_hist, weather_hist)
    
    # Get multi-output prediction (returns an array of 'hours' length)
    raw_preds = MODEL.predict(X)[0] 

    forecast_dict = {}
    for i in range(hours):
        h_idx = i + 1  # 1-based indexing for the orchestrator
        prediction = raw_preds[i]
        
        # Calculate the actual wall-clock hour for night gating
        future_dt = trigger_time + timedelta(hours=h_idx)
        
        # Hard Night Gating logic
        if future_dt.hour < 6 or future_dt.hour > 19:
            val = 0.0
        else:
            val = max(0, float(prediction))
            
        forecast_dict[h_idx] = val
        
    return forecast_dict

# ---------------- TESTING -------------------
if __name__ == "__main__":
    FORECAST_HORIZON = 6
    # Simulated trigger time
    trigger_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    # Calling it like your orchestrator snippet
    solar_fc = get_solar_forecast(trigger_time, hours=FORECAST_HORIZON)
    
    print(f"Trigger Time: {trigger_time}")
    print("Solar Forecast Array:", solar_fc)
    
    # Verify it works with your list comprehension:
    forecast_data = []
    for h in range(1, FORECAST_HORIZON + 1):
        solar = solar_fc[h]
        # (Assuming load_fc is similar)
        forecast_data.append({
            "t_plus_hours": h,
            "forecast_solar_mwh": round(solar, 2)
        })
    print("Formatted for Orchestrator:", forecast_data)