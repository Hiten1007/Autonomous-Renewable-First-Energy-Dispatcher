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

# ------------- WEATHER FETCH -------------
def fetch_live_weather_history():
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{','.join(LOCATIONS)}/last24hours"
    params = {
        "unitGroup": "metric",
        "include": "hours",
        "key": API_KEY,
        "contentType": "json"
    }

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

# --------- VIRTUAL SOLAR SENSOR ----------
def estimate_solar(weather_hist):
    records = []
    for dt, row in weather_hist.iterrows():
        hour = dt.hour
        if 6 <= hour <= 18:
            daily_cycle = np.sin((hour - 6) * np.pi / 12)
        else:
            daily_cycle = 0

        solar = MAX_SOLAR_MWh * daily_cycle * row["ALLSKY_KT_HOURLY"]
        records.append({"datetime": dt, "solar_mwh": max(0, solar)})

    return pd.DataFrame(records).set_index("datetime")

# -------- FEATURE VECTOR CREATION --------
def create_feature_vector(t, solar_hist, weather_hist):
    hour_sin = np.sin(2 * np.pi * t.hour / 24)
    hour_cos = np.cos(2 * np.pi * t.hour / 24)
    month_sin = np.sin(2 * np.pi * t.month / 12)
    month_cos = np.cos(2 * np.pi * t.month / 12)

    is_day = 1 if 6 <= t.hour <= 18 else 0

    def lag(h):
        return solar_hist.asof(t - timedelta(hours=h))["solar_mwh"]

    solar_lag_1h  = lag(1)
    solar_lag_3h  = lag(3)
    solar_lag_6h  = lag(6)
    solar_lag_24h = lag(24)

    end = t - timedelta(seconds=1)
    solar_roll3h  = solar_hist.loc[end - timedelta(hours=3):end]["solar_mwh"].mean()
    solar_roll24h = solar_hist.loc[end - timedelta(hours=24):end]["solar_mwh"].mean()

    wx = weather_hist.asof(t)

    # -------- HARD NIGHT GATING --------
    if not is_day:
        solar_lag_1h = solar_lag_3h = solar_lag_6h = solar_lag_24h = 0
        solar_roll3h = solar_roll24h = 0
        kt = 0.0
        temp = wx["T2M_HOURLY"] * 0.2
        wind = wx["WS10M_HOURLY"] * 0.2
    else:
        kt = wx["ALLSKY_KT_HOURLY"]
        temp = wx["T2M_HOURLY"]
        wind = wx["WS10M_HOURLY"]

    return pd.DataFrame({
        "hour_sin": [hour_sin],
        "hour_cos": [hour_cos],
        "month_sin": [month_sin],
        "month_cos": [month_cos],
        "LAT": [AVG_LAT],
        "LON": [AVG_LON],
        "is_day": [is_day],
        "solar_lag_1h": [solar_lag_1h],
        "solar_lag_3h": [solar_lag_3h],
        "solar_lag_6h": [solar_lag_6h],
        "solar_lag_24h": [solar_lag_24h],
        "solar_roll3h": [solar_roll3h],
        "solar_roll24h": [solar_roll24h],
        "ALLSKY_KT_HOURLY": [kt],
        "T2M_HOURLY": [temp],
        "WS10M_HOURLY": [wind],
    })

# ---------------- MAIN -------------------
if __name__ == "__main__":
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    weather_hist = fetch_live_weather_history()
    solar_hist = estimate_solar(weather_hist)

    now = (datetime.now() - timedelta(days=-1)).replace(
        hour=15, minute=0, second=0, microsecond=0
    )
    X = create_feature_vector(now, solar_hist, weather_hist)

    X[["LAT", "LON"]] = scaler.transform(X[["LAT", "LON"]])

    preds = model.predict(X)[0]

    print("\n☀️ Solar forecast (next 6 hours):")
    for i, v in enumerate(preds, 1):
        hour = (now + timedelta(hours=i)).hour
        if hour < 6 or hour > 19:
            v = 0.0
        print(f"Hour +{i}: {max(0, v):.2f} MWh")
