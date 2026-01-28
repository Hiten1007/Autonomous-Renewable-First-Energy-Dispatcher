import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta

MODEL_PATH = "fixed_load_meter_model.pkl"
DATA_PATH = "haryana_hourly_generation_preprocessed.csv"


def create_features(ts: pd.Timestamp, load_now: float, load_lag_1h: float,
                    load_lag_24h: float, load_lag_168h: float):
    hour = ts.hour
    weekday = ts.weekday()
    month = ts.month

    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    dow_sin = np.sin(2 * np.pi * weekday / 7)
    dow_cos = np.cos(2 * np.pi * weekday / 7)
    is_weekend = weekday >= 5

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
    Return nearest past load values for given timestamp.
    """
    df = df.sort_values(["Year", "Month", "Day", "Hour_of_day"]).reset_index(drop=True)

    # Convert dataset to datetime
    df["timestamp"] = pd.to_datetime(df["Year"].astype(str) + "-" +
                                     df["Month"].astype(str).str.zfill(2) + "-" +
                                     df["Day"].astype(str).str.zfill(2) + " " +
                                     df["Hour_of_day"].astype(str).str.zfill(2) + ":00:00")

    # Filter past records
    past_df = df[df["timestamp"] <= ts]

    if past_df.empty:
        raise ValueError("No past data available for this timestamp.")

    # Find nearest past timestamp index
    nearest_idx = past_df.index[-1]

    load_now = float(df.loc[nearest_idx, "Demand_MWh"])

    # Lags
    lag1 = float(df.loc[nearest_idx - 1, "Demand_MWh"]) if nearest_idx >= 1 else np.nan
    lag24 = float(df.loc[nearest_idx - 24, "Demand_MWh"]) if nearest_idx >= 24 else np.nan
    lag168 = float(df.loc[nearest_idx - 168, "Demand_MWh"]) if nearest_idx >= 168 else np.nan

    return load_now, lag1, lag24, lag168


def forecast(timestamp_str: str):
    ts = pd.to_datetime(timestamp_str)

    # Load data
    df = pd.read_csv(DATA_PATH)

    load_now, lag1, lag24, lag168 = get_nearest_past_load(df, ts)

    X = create_features(ts, load_now, lag1, lag24, lag168)

    model = joblib.load(MODEL_PATH)

    y_pred = model.predict(X)[0]

    result = []
    for i in range(6):
        result.append({
            "Hour Ahead": f"{i + 1}h",
            "Timestamp": (ts + timedelta(hours=i + 1)).strftime("%Y-%m-%d %H:%M:%S"),
            "Forecast (MWh)": round(float(y_pred[i]), 2)
        })

    return pd.DataFrame(result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ts", type=str, required=True,
                        help="Timestamp in format YYYY-MM-DD HH (or any pandas parseable format)")
    args = parser.parse_args()

    df_forecast = forecast(args.ts)
    print(df_forecast.to_string(index=False))
