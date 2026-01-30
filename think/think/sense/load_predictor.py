import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta


import os
import joblib
from pathlib import Path

# 1. Get the directory where THIS script is located
BASE_DIR = Path(__file__).resolve().parent

# 2. Define the model path relative to this script
MODEL_PATH = BASE_DIR / "fixed_load_meter_model.pkl"

# 3. Load using the absolute path
try:
    load_model = joblib.load(MODEL_PATH)
    print(f"✅ Load Model loaded successfully from: {MODEL_PATH}")
except FileNotFoundError:
    print(f"❌ Still can't find the model at: {MODEL_PATH.absolute()}")
LOAD_DATA_PATH = BASE_DIR /"haryana_hourly_generation_preprocessed.csv"

# Load model once globally
def create_load_features(ts: pd.Timestamp, load_now: float, load_lag_1h: float,
                         load_lag_24h: float, load_lag_168h: float):
    """Creates the feature vector for the multi-output load model."""
    hour = ts.hour
    weekday = ts.weekday()
    month = ts.month

    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    dow_sin = np.sin(2 * np.pi * weekday / 7)
    dow_cos = np.cos(2 * np.pi * weekday / 7)
    is_weekend = 1 if weekday >= 5 else 0

    return pd.DataFrame([{
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "dow_sin": dow_sin,
        "dow_cos": dow_cos,
        "Weekday": weekday,
        "Is_Weekend": is_weekend,
        "Month": month,
        "load_now": load_now,
        "load_lag_1h": load_lag_1h,
        "load_lag_24h": load_lag_24h,
        "load_lag_168h": load_lag_168h
    }])

def get_nearest_past_load(df, ts):
    """
    Finds the historical load values based on the trigger timestamp.
    """
    # Filter past records
    past_df = df[df["timestamp"] <= ts]

    if past_df.empty:
        # Fallback if the requested timestamp is earlier than our CSV data
        return 0.0, 0.0, 0.0, 0.0

    # Find nearest past timestamp index
    nearest_idx = past_df.index[-1]

    load_now = float(df.loc[nearest_idx, "Demand_MWh"])

    # Safely get lags using positional indexing
    def get_val(idx_offset):
        target_idx = nearest_idx - idx_offset
        if target_idx >= 0:
            return float(df.loc[target_idx, "Demand_MWh"])
        return load_now # Fallback to current load if lag doesn't exist

    lag1 = get_val(1)
    lag24 = get_val(24)
    lag168 = get_val(168)

    return load_now, lag1, lag24, lag168

# -------- NEW ORCHESTRATOR COMPATIBLE FUNCTION --------
def get_load_forecast(trigger_time, hours=6):
    """
    Produces a dictionary where keys are 1 to 'hours' and values are MWh.
    Compatible with: load_fc = get_load_forecast(trigger_time, hours=6)
    """
    # Convert trigger_time to pandas Timestamp if it's a datetime object
    ts = pd.to_datetime(trigger_time)

    # Load and preprocess data
    df = pd.read_csv(LOAD_DATA_PATH)
    
    # Pre-construct timestamps for faster lookup
    df["timestamp"] = pd.to_datetime(df["Year"].astype(str) + "-" +
                                     df["Month"].astype(str).str.zfill(2) + "-" +
                                     df["Day"].astype(str).str.zfill(2) + " " +
                                     df["Hour_of_day"].astype(str).str.zfill(2) + ":00:00")
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Get historical features based on trigger time
    load_now, lag1, lag24, lag168 = get_nearest_past_load(df, ts)

    # Create input vector
    X = create_load_features(ts, load_now, lag1, lag24, lag168)

    # Predict (assumes multi-output model returning array of size 'hours')
    y_pred = load_model.predict(X)[0]

    # Format into a 1-indexed dictionary
    forecast_dict = {}
    for i in range(hours):
        # The model predicts i+1 hours ahead
        val = float(y_pred[i])
        forecast_dict[i + 1] = round(max(0, val), 2)

    return forecast_dict

# ---------------- TESTING -------------------
if __name__ == "__main__":
    # Example trigger time
    trigger_time = datetime(2026, 2, 18, 15, 0) # Replace with a valid date from your CSV
    
    FORECAST_HORIZON = 6
    
    # Calling it like the orchestrator
    load_fc = get_load_forecast(trigger_time, hours=FORECAST_HORIZON)
    
    print(f"Trigger Time: {trigger_time}")
    print("Load Forecast Array:", load_fc)
    
    # Example of how it fits into your main orchestrator loop:
    forecast_data = []
    for h in range(1, FORECAST_HORIZON + 1):
        load = load_fc[h]
        forecast_data.append({
            "t_plus_hours": h,
            "forecast_load_mwh": load
        })
    print("\nFormatted for Orchestrator:")
    print(forecast_data)