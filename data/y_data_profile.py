import pandas as pd
from ydata_profiling import ProfileReport

# Load your final dataset
df = pd.read_csv("FINAL_ALL_FEATURES.csv")

# Create report
profile = ProfileReport(
    df,
    title="FINAL_ALL_FEATURES Data Profile",
    explorative=True
)

# Save report to HTML
profile.to_file("FINAL_ALL_FEATURES_PROFILE.html")

print("✅ HTML Report Generated: FINAL_ALL_FEATURES_PROFILE.html")
