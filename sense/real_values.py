import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
START_DATE = "2026-05-02"
DAYS = 7                      # simulate 7 days
INTERVAL_MIN = 30

SOLAR_MAX_MWH = 9000           # region-scale
LOAD_BASE_MIN = 500
LOAD_BASE_MAX = 6000
NOISE_STD = 0.05               # 5% noise
# ---------------------------------------

def seasonal_factor(month):
    # Higher solar in summer, lower in winter
    return {
        1: 0.6, 2: 0.65, 3: 0.75,
        4: 0.9, 5: 1.0, 6: 1.05,
        7: 1.05, 8: 1.0, 9: 0.9,
        10: 0.8, 11: 0.7, 12: 0.6
    }[month]

def solar_generation(hour, month):
    if hour < 6 or hour > 18:
        return 0.0

    # Normalized bell curve (sun path)
    x = (hour - 6) / 12
    base = np.sin(np.pi * x)

    solar = base * SOLAR_MAX_MWH * seasonal_factor(month)
    solar *= np.random.normal(1, NOISE_STD)

    return max(0, solar)

def load_generation(hour, month):
    # Daily load pattern
    if 6 <= hour <= 9:
        factor = 1.2
    elif 18 <= hour <= 22:
        factor = 1.3
    else:
        factor = 0.9

    seasonal = 1 + 0.1 * np.cos((month - 6) * np.pi / 6)
    base_load = np.random.uniform(LOAD_BASE_MIN, LOAD_BASE_MAX)

    load = base_load * factor * seasonal
    load *= np.random.normal(1, NOISE_STD)

    return max(LOAD_BASE_MIN, load)

# ---------------- GENERATION ----------------
rows = []
current = datetime.fromisoformat(START_DATE)
end_time = current + timedelta(days=DAYS)

while current < end_time:
    hour = current.hour + current.minute / 60
    month = current.month

    solar = solar_generation(hour, month) / 2   # 30-min energy
    load = load_generation(hour, month) / 2

    rows.append({
        "timestamp": current,
        "solar_MWh_30min": round(solar, 2),
        "load_MWh_30min": round(load, 2)
    })

    current += timedelta(minutes=INTERVAL_MIN)

df = pd.DataFrame(rows)
df.to_csv("simulated_30min_solar_load.csv", index=False)

print("Generated:", len(df), "rows")
print(df.head())
