import pandas as pd

df = pd.read_csv("FINAL_ALL_FEATURES.csv") \
       .drop(columns=["CLRSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "WD10M", "WS10M"]) \

df.to_csv("FINAL_ALL_FEATURES_CLEANED.csv", index=False)