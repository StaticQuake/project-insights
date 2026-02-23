import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

master_path = DATA_DIR / "movies_master.csv"

# Read pipe-separated master file
movies_df = pd.read_csv(master_path, sep="|")

# Pick only the metric columns you want
metrics_df = movies_df[[
    "id",
    "popularity",
    "vote_average",
    "vote_count"
]].copy()

# Add snapshot_date column manually
SNAPSHOT_DATE = "2026-02-02"
metrics_df["snapshot_date"] = SNAPSHOT_DATE

# Reorder columns to match your metrics schema
metrics_df = metrics_df[[
    "id",
    "snapshot_date",
    "popularity",
    "vote_average",
    "vote_count"
]]

# Save as metrics CSV
output_path = DATA_DIR / "metrics_2026-02-02.csv"
metrics_df.to_csv(output_path, index=False)

print(f"✅ Saved: {output_path}")