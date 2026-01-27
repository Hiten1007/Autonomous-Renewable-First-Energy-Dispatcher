import os
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from functools import reduce

# =============================
# CONFIG
# =============================
BASE_DIR = os.getcwd()
K_NEIGHBORS = 4

# 🔒 EXPLICIT FEATURE FOLDER LIST (YOU CONTROL THIS)
FEATURE_FOLDERS = [
    "All Sky Surface Shortwave Downward Irradiance",
    "CI",
    "TEMP",
    "WIND SPEED"
]

KEY_COLS = ["LAT", "LON", "YEAR", "MO", "DY"]

# =============================
# STEP 1: LOAD FEATURES SAFELY
# =============================
feature_data = {}   # feature_name -> dataframe

for folder in FEATURE_FOLDERS:
    folder_path = os.path.join(BASE_DIR, folder)

    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"❌ Missing folder: {folder}")

    dfs = []
    for file in sorted(os.listdir(folder_path)):
        if file.endswith(".csv"):
            df = pd.read_csv(
                os.path.join(folder_path, file),
                header=9
            )
            dfs.append(df)

    if not dfs:
        raise ValueError(f"❌ No CSV files found in {folder}")

    full_df = pd.concat(dfs, ignore_index=True)

    # Identify feature column safely
    feature_cols = [c for c in full_df.columns if c not in KEY_COLS]

    if len(feature_cols) != 1:
        raise ValueError(
            f"❌ Folder '{folder}' has ambiguous feature columns: {feature_cols}"
        )

    feature_col = feature_cols[0]

    if feature_col in feature_data:
        raise ValueError(f"❌ Duplicate feature detected: {feature_col}")

    feature_data[feature_col] = full_df

    print(f"✅ Loaded feature: {feature_col} ({len(full_df)} rows)")

print(f"\n📦 Total features loaded: {len(feature_data)}")

# =============================
# STEP 2: MASTER GRID
# =============================
master_grid = (
    pd.concat(
        [df[KEY_COLS] for df in feature_data.values()],
        ignore_index=True
    )
    .drop_duplicates()
    .sort_values(KEY_COLS)
    .reset_index(drop=True)
)

print(f"🌍 Master grid size: {len(master_grid)}")

# =============================
# STEP 3: SPATIAL FILL FUNCTION
# =============================
def spatial_fill_feature(feature_df, feature_col, master_grid):
    filled_days = []

    for (year, mo, dy), day_grid in master_grid.groupby(["YEAR", "MO", "DY"]):
        day_data = feature_df[
            (feature_df["YEAR"] == year) &
            (feature_df["MO"] == mo) &
            (feature_df["DY"] == dy)
        ]

        merged = day_grid.merge(
            day_data,
            on=KEY_COLS,
            how="left"
        )

        known = merged.dropna(subset=[feature_col])
        missing = merged[merged[feature_col].isna()]

        if not known.empty and not missing.empty:
            tree = cKDTree(known[["LAT", "LON"]].values)
            k = min(K_NEIGHBORS, len(known))

            distances, indices = tree.query(
                missing[["LAT", "LON"]].values,
                k=k
            )

            if k == 1:
                distances = distances[:, None]
                indices = indices[:, None]

            distances = np.maximum(distances, 1e-6)
            known_values = known[feature_col].to_numpy()
            values = known_values[indices]

            weights = 1 / distances
            interpolated = np.sum(weights * values, axis=1) / np.sum(weights, axis=1)

            merged.loc[missing.index, feature_col] = interpolated

        filled_days.append(merged)

    return pd.concat(filled_days, ignore_index=True)

# =============================
# STEP 4: FILL EACH FEATURE
# =============================
filled_features = []

for feature_col, df in feature_data.items():
    print(f"🔧 Spatial filling: {feature_col}")
    filled_df = spatial_fill_feature(df, feature_col, master_grid)

    filled_df = filled_df[KEY_COLS + [feature_col]]
    filled_features.append(filled_df)

# =============================
# STEP 5: SAFE MERGE (INNER ON GRID)
# =============================
final_df = reduce(
    lambda left, right: left.merge(
        right,
        on=KEY_COLS,
        how="inner",
        validate="one_to_one"
    ),
    filled_features
)

# =============================
# STEP 6: SAVE
# =============================
final_df.to_csv("FINAL_ALL_FEATURES.csv", index=False)

print("\n🎉 PIPELINE COMPLETE")
print(f"📁 Output: FINAL_ALL_FEATURES.csv")
print(f"📊 Shape: {final_df.shape}")
