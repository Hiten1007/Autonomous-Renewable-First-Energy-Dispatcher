import numpy as np
from datetime import datetime

# ---------------- CONFIG ----------------
SOLAR_MAX_MWH = 9000
LOAD_BASE_MIN = 500
LOAD_BASE_MAX = 6000
NOISE_STD = 0.05
# ---------------------------------------

def seasonal_factor(month):
    return {
        1: 0.6, 2: 0.65, 3: 0.75,
        4: 0.9, 5: 1.0, 6: 1.05,
        7: 1.05, 8: 1.0, 9: 0.9,
        10: 0.8, 11: 0.7, 12: 0.6
    }[month]

def solar_generation(hour, month):
    if hour < 6 or hour > 18:
        return 0.0

    x = (hour - 6) / 12
    base = np.sin(np.pi * x)

    solar = base * SOLAR_MAX_MWH * seasonal_factor(month)
    solar *= np.random.normal(1, NOISE_STD)

    return max(0, solar)

def load_generation(hour, month):
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

# ---------------- ACTUALS SIMULATOR ----------------

def get_current_actuals(trigger_time: datetime):
    hour = trigger_time.hour + trigger_time.minute / 60
    month = trigger_time.month

    # 30-min energy
    solar_30min = solar_generation(hour, month) / 2
    load_30min = load_generation(hour, month) / 2

    return {
        "solar_mwh": round(solar_30min, 2),
        "load_mwh": round(load_30min, 2),
    }
