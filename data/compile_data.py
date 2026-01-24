import os
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from functools import reduce

BASE_DIR = os.getcwd()
K_NEIGHBORS = 4

# ---------- STEP 1: LOAD ALL FEATURES ----------
feature_data = {}  # feature_name -> dataframe

for feature_folder in os.listdir(BASE_DIR):
    folder_path = os.path.join(BASE_DIR, feature_folder)

    if not os.path.isdir(folder_path):
        continue

    dfs = []
    for file in sorted(os.listdir(folder_path)):
        if file.endswith(".csv"):
            df = pd.read_csv(
                os.path.join(folder_path, file),
                header=9   # 0-based index → line 10
            )
            dfs.append(df)

    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)

        # safer feature column extraction
        feature_col = [c for c in full_df.columns if c not in ["LAT", "LON", "YEAR", "MO", "DY"]][0]

        feature_data[feature_col] = full_df

print(f"📦 Loaded {len(feature_data)} features")

# ---------- STEP 2: BUILD MASTER SPATIO-TEMPORAL GRID ----------
master_grid = pd.concat(
    [
        df[["LAT", "LON", "YEAR", "MO", "DY"]]
        for df in feature_data.values()
    ],
    ignore_index=True
).drop_duplicates()

print(f"🌍 Master grid size: {len(master_grid)} rows")

# ---------- STEP 3: SPATIAL FILL PER FEATURE ----------
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
            on=["LAT", "LON", "YEAR", "MO", "DY"],
            how="left"
        )

        known = merged.dropna(subset=[feature_col])
        missing = merged[merged[feature_col].isna()]

        # Only spatial interpolation if some data exists that day
        if not known.empty and not missing.empty:
            tree = cKDTree(known[["LAT", "LON"]].values)
            k = min(K_NEIGHBORS, len(known))

            distances, indices = tree.query(
                missing[["LAT", "LON"]].values,
                k=k
            )

            # fix for k=1 case
            if k == 1:
                distances = distances[:, None]
                indices = indices[:, None]

            distances = np.maximum(distances, 1e-6)

            # SAFE indexing using numpy
            known_values = known[feature_col].to_numpy()
            values = known_values[indices]

            weights = 1 / distances
            interpolated = np.sum(weights * values, axis=1) / np.sum(weights, axis=1)

            merged.loc[missing.index, feature_col] = interpolated

        filled_days.append(merged)

    return pd.concat(filled_days, ignore_index=True)

filled_features = []

for feature_col, df in feature_data.items():
    print(f"🔧 Filling feature: {feature_col}")
    filled_df = spatial_fill_feature(df, feature_col, master_grid)

    # keep only needed columns
    filled_df = filled_df[["LAT", "LON", "YEAR", "MO", "DY", feature_col]]
    filled_features.append(filled_df)

# ---------- STEP 4: MERGE ALL FEATURES ----------
final_df = reduce(
    lambda left, right: left.merge(
        right,
        on=["LAT", "LON", "YEAR", "MO", "DY"],
        how="inner"
    ),
    filled_features
)

# ---------- STEP 5: SAVE ----------
final_df.to_csv("FINAL_ALL_FEATURES.csv", index=False)

print("🎉 DONE")
print(f"📁 Output: FINAL_ALL_FEATURES.csv")
print(f"📊 Shape: {final_df.shape}")
