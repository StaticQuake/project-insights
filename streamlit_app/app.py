import streamlit as st
import pandas as pd
from pyathena import connect

# Page config
st.set_page_config(
    page_title="Project Insights",
    page_icon="📊",
    layout="wide"
)

# Athena connection
@st.cache_resource
def get_connection():
    return connect(
        s3_staging_dir="s3://project-insights-data-sem6/athena-results/",
        region_name=st.secrets["aws"]["region_name"],
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"]
    )

@st.cache_data(ttl=3600)
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

# Title
st.title("📊 Project Insights")
st.caption("Daily movie analytics powered by TMDB + AWS")

# Sidebar
st.sidebar.title("Filters")
content_type = st.sidebar.selectbox("Content Type", ["Movies"])

# ── STAT CARDS ──
st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

total = run_query("SELECT COUNT(DISTINCT id) as total FROM project_insights.daily_metrics")
col1.metric("Total Tracked", f"{total['total'][0]:,}")

top_movie = run_query("""
    SELECT m.title, d.popularity 
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.popularity DESC LIMIT 1
""")
col2.metric("Most Popular Today", top_movie['title'][0], f"{top_movie['popularity'][0]:.1f}")

latest_date = run_query("SELECT MAX(snapshot_date) as dt FROM project_insights.daily_metrics")
col3.metric("Latest Snapshot", latest_date['dt'][0])

days = run_query("SELECT COUNT(DISTINCT snapshot_date) as days FROM project_insights.daily_metrics")
col4.metric("Days of Data", days['days'][0])

st.divider()

# ── TOP 10 ──
st.subheader("🔥 Top 10 Most Popular Movies Today")

top10 = run_query("""
    SELECT m.title, m.release_year, d.popularity, d.vote_average, d.vote_count
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.popularity DESC
    LIMIT 10
""")

import plotly.express as px
fig = px.bar(
    top10, x="popularity", y="title",
    orientation="h",
    color="popularity",
    color_continuous_scale="Blues",
    labels={"popularity": "Popularity Score", "title": "Movie"}
)
fig.update_layout(yaxis=dict(autorange="reversed"), height=400, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TREND EXPLORER ──
st.subheader("📈 Trend Explorer")

search = st.text_input("Search a movie", placeholder="e.g. Tenet")

if search:
    movie_list = run_query(f"""
        SELECT DISTINCT m.id, m.title 
        FROM project_insights.movies_master m
        WHERE LOWER(m.title) LIKE LOWER('%{search}%')
        LIMIT 10
    """)

    if movie_list.empty:
        st.warning("No movies found.")
    else:
        selected = st.selectbox("Select movie", movie_list['title'].tolist())
        movie_id = movie_list[movie_list['title'] == selected]['id'].values[0]

        trend = run_query(f"""
            SELECT snapshot_date, popularity, vote_average, vote_count
            FROM project_insights.daily_metrics
            WHERE id = {movie_id}
            ORDER BY snapshot_date
        """)
        trend['snapshot_date'] = trend['snapshot_date'].astype(str)
        col1, col2 = st.columns(2)
        with col1:
            fig2 = px.line(trend, x="snapshot_date", y="popularity", title="Popularity Trend", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            fig3 = px.line(trend, x="snapshot_date", y="vote_count", title="Vote Count Growth", markers=True)
            st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── AVG POPULARITY BY YEAR ──
st.subheader("📅 Average Popularity by Release Year")

by_year = run_query("""
    SELECT m.release_year, AVG(d.popularity) as avg_popularity, COUNT(DISTINCT d.id) as movie_count
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    GROUP BY m.release_year
    ORDER BY m.release_year
""")

fig4 = px.bar(
    by_year, x="release_year", y="avg_popularity",
    color="avg_popularity",
    color_continuous_scale="Blues",
    labels={"release_year": "Release Year", "avg_popularity": "Avg Popularity"},
    text="movie_count"
)
fig4.update_traces(texttemplate='%{text} movies', textposition='outside')
fig4.update_layout(height=400, showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# # ── AVG RATING BY GENRE ──
# st.subheader("🎬 Average Rating by Genre")

# by_genre = run_query("""
#     SELECT m.genre_ids, AVG(d.vote_average) as avg_rating, COUNT(DISTINCT d.id) as movie_count
#     FROM project_insights.daily_metrics d
#     JOIN project_insights.movies_master m ON d.id = m.id
#     WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
#     GROUP BY m.genre_ids
#     ORDER BY avg_rating DESC
#     LIMIT 15
# """)

# fig5 = px.bar(
#     by_genre, x="avg_rating", y="genre_ids",
#     orientation="h",
#     color="avg_rating",
#     color_continuous_scale="Greens",
#     labels={"avg_rating": "Avg Rating", "genre_ids": "Genre"}
# )
# fig5.update_layout(yaxis=dict(autorange="reversed"), height=500, showlegend=False)
# st.plotly_chart(fig5, use_container_width=True)

# st.divider()

# ── TOP 10 BY VOTE COUNT ──
st.subheader("⭐ Top 10 Most Voted Movies")

top_voted = run_query("""
    SELECT m.title, m.release_year, d.vote_count, d.vote_average
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.vote_count DESC
    LIMIT 10
""")

fig5 = px.bar(
    top_voted, x="vote_count", y="title",
    orientation="h",
    color="vote_average",
    color_continuous_scale="Oranges",
    labels={"vote_count": "Total Votes", "title": "Movie", "vote_average": "Rating"}
)
fig5.update_layout(yaxis=dict(autorange="reversed"), height=400, showlegend=False)
st.plotly_chart(fig5, use_container_width=True)