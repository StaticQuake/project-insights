import boto3
import pandas as pd
from pyathena import connect

conn = connect(
    s3_staging_dir="s3://project-insights-data-sem6/athena-results/",
    region_name="us-east-1"
)

df = pd.read_sql("SELECT MAX(snapshot_date) as dt FROM project_insights.daily_metrics", conn)
print(df)