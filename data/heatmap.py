import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("./solar_energy/HOURLY_SOLAR_DATA_PREPROCESSED.csv")

# Compute correlation
corr = df.corr()

plt.figure(figsize=(12, 10))
sns.heatmap(corr, annot=False, cmap="viridis")
plt.title("Feature Correlation Heatmap")
plt.show()
