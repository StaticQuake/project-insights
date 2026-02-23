# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from pathlib import Path

# st.set_page_config(page_title="Movie Analytics", layout="wide")
# st.title("🎬 Movie Analytics Dashboard")

# BASE_DIR = Path(__file__).parent
# DATA_DIR = BASE_DIR / "data"

# # ---- Load master movie data (pipe-separated) ----
# movies_master_path = DATA_DIR / "movies_master.csv"
# if not movies_master_path.exists():
#     st.error("❌ movies_master.csv not found in data/ folder")
#     st.stop()

# movies_df = pd.read_csv(movies_master_path, sep="|")

# # If your ID column is named differently, fix it here:
# # movies_df.rename(columns={"movie_id": "id"}, inplace=True)

# # ---- Load all metrics files ----
# csv_files = sorted(DATA_DIR.glob("metrics_*.csv"))
# if not csv_files:
#     st.error("❌ No metrics_*.csv files found in data/ folder")
#     st.stop()

# dfs = []
# for file in csv_files:
#     df = pd.read_csv(file)
#     df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
#     df["source"] = file.stem  # metrics_2026-02-20
#     dfs.append(df)

# metrics_df = pd.concat(dfs, ignore_index=True)
# # Remove metric-like columns from movies_master to avoid _x/_y mess
# cols_to_drop = ["popularity", "vote_average", "vote_count", "source"]
# movies_df = movies_df.drop(columns=[c for c in cols_to_drop if c in movies_df.columns])
# # ---- Join metrics with movie master ----
# df_all = metrics_df.merge(movies_df, on="id", how="left")

# # ---- UI Filters ----
# titles = df_all["title"].dropna().unique()
# selected_title = st.selectbox("Search / Select Movie Title", sorted(titles))

# metric = st.selectbox("Select Metric", ["popularity", "vote_average", "vote_count"])

# selected_movie_df = df_all[df_all["title"] == selected_title]

# col1, col2 = st.columns(2)

# with col1:
#     fig_line = px.line(
#         selected_movie_df,
#         x="snapshot_date",
#         y=metric,
#         color="source",
#         markers=True,
#         title=f"{metric.replace('_', ' ').title()} Trend for {selected_title}"
#     )
#     st.plotly_chart(fig_line, use_container_width=True)

# with col2:
#     fig_bar = px.bar(
#         selected_movie_df,
#         x="snapshot_date",
#         y="vote_count",
#         color="source",
#         barmode="group",
#         title="Vote Count Comparison"
#     )
#     st.plotly_chart(fig_bar, use_container_width=True)

# # ---- Movie details ----
# st.divider()
# st.subheader("🎥 Movie Details")

# detail_cols = [c for c in ["title", "overview", "genre_id"] if c in selected_movie_df.columns]
# if detail_cols:
#     st.table(selected_movie_df[detail_cols].drop_duplicates())
# else:
#     st.info("No movie detail columns found to display.")

# # ---- Month-wise snapshots ----
# df_all["month"] = df_all["snapshot_date"].dt.to_period("M").astype(str)
# month_counts = df_all.groupby(["month", "source"]).size().reset_index(name="count")

# fig_month = px.bar(
#     month_counts,
#     x="month",
#     y="count",
#     color="source",
#     barmode="group",
#     title="Number of Snapshots per Month"
# )
# st.plotly_chart(fig_month, use_container_width=True)


import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Movie Analytics", layout="wide")
st.title("🎬 Movie Analytics Dashboard")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ---- Load master movie data (pipe-separated) ----
movies_master_path = DATA_DIR / "movies_master.csv"
if not movies_master_path.exists():
    st.error("❌ movies_master.csv not found in data/ folder")
    st.stop()

movies_df = pd.read_csv(movies_master_path, sep="|")

# ---- Load all metrics files ----
csv_files = sorted(DATA_DIR.glob("metrics_*.csv"))
if not csv_files:
    st.error("❌ No metrics_*.csv files found in data/ folder")
    st.stop()

dfs = []
for file in csv_files:
    df = pd.read_csv(file)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    df["source"] = file.stem  # metrics_2026-02-20

    # Ensure numeric
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce")
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce")

    dfs.append(df)

metrics_df = pd.concat(dfs, ignore_index=True)

# ---- Remove duplicate metric columns from master to avoid _x/_y ----
cols_to_drop = ["popularity", "vote_average", "vote_count", "source"]
movies_df = movies_df.drop(columns=[c for c in cols_to_drop if c in movies_df.columns])

# ---- Fix ID dtype (important for merge) ----
metrics_df["id"] = metrics_df["id"].astype(int)
movies_df["id"] = movies_df["id"].astype(int)

# ---- Join ----
df_all = metrics_df.merge(movies_df, on="id", how="left")

# ---- UI Filters ----
titles = df_all["title"].dropna().unique()
selected_title = st.selectbox("Search / Select Movie Title", sorted(titles))
metric = st.selectbox("Select Metric", ["popularity", "vote_average", "vote_count"])

selected_movie_df = df_all[df_all["title"] == selected_title]

# ---- IMPORTANT: Aggregate to one point per day per source + sort ----
plot_df = (
    selected_movie_df
    .groupby(["snapshot_date", "source"], as_index=False)[metric]
    .mean()
    .sort_values("snapshot_date")
)

col1, col2 = st.columns(2)

with col1:
    if plot_df.empty:
        st.warning("No metric data available for this movie.")
    else:
        fig_line = px.line(
            plot_df,
            x="snapshot_date",
            y=metric,
            title=f"{metric.replace('_', ' ').title()} Trend for {selected_title}"
        )
        # Force visible line + dots so slope is obvious
        fig_line.update_traces(mode="lines+markers", line=dict(width=3), marker=dict(size=7))
        st.plotly_chart(fig_line, use_container_width=True)

with col2:
    if not selected_movie_df.empty:
        fig_bar = px.bar(
            selected_movie_df,
            x="snapshot_date",
            y="vote_count",
            color="source",
            barmode="group",
            title="Vote Count Comparison"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ---- Movie details ----
st.divider()
st.subheader("🎥 Movie Details")

detail_cols = [c for c in ["title", "overview", "genre_ids"] if c in selected_movie_df.columns]
if detail_cols and not selected_movie_df.empty:
    st.table(selected_movie_df[detail_cols].drop_duplicates())
else:
    st.info("No movie detail columns found to display.")

# ---- Month-wise snapshots ----
df_all["month"] = df_all["snapshot_date"].dt.to_period("M").astype(str)
month_counts = df_all.groupby(["month", "source"]).size().reset_index(name="count")

fig_month = px.bar(
    month_counts,
    x="month",
    y="count",
    color="source",
    barmode="group",
    title="Number of Snapshots per Month"
)
st.plotly_chart(fig_month, use_container_width=True)