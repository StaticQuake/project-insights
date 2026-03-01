import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyathena import connect

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="Project Insights",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ──
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { color: #ffffff; font-size: 2.2rem !important; font-weight: 800 !important; }
    h2, h3 { color: #e2e8f0 !important; }
    .stMetric { background: #1e2130; border-radius: 12px; padding: 16px; border: 1px solid #2d3748; }
    .stMetric label { color: #a0aec0 !important; font-size: 13px !important; font-weight: 600 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.6rem !important; }
    .stMetric [data-testid="stMetricDelta"] { color: #68d391 !important; }
    div[data-testid="stSelectbox"] label { color: #a0aec0 !important; }
    .stTextInput input { background: #1e2130 !important; color: #ffffff !important; border: 1px solid #2d3748 !important; border-radius: 8px !important; }
    .stSelectbox select { background: #1e2130 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b27 !important; }
    [data-testid="stSidebar"] h1 { font-size: 1.2rem !important; }
    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
    hr { border-color: #2d3748 !important; }
    .caption-text { color: #718096; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── GENRE MAPPING ──
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western"
}

def parse_genre(genre_str):
    """Parse genre_ids string like '[28, 12, 878]' and return first genre name."""
    try:
        ids = [int(x.strip()) for x in genre_str.strip("[]").split(",")]
        for gid in ids:
            if gid in GENRE_MAP:
                return GENRE_MAP[gid]
    except:
        pass
    return "Other"

# ── ATHENA CONNECTION ──
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

# ── SIDEBAR ──
with st.sidebar:
    st.title("🎬 Project Insights")
    st.markdown("---")
    st.caption("CONTENT TYPE")
    content_type = st.selectbox("", ["Movies"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("ABOUT")
    st.markdown("""
    <div style='color: #718096; font-size: 12px; line-height: 1.7;'>
    Daily analytics powered by<br>
    <b style='color:#a0aec0'>TMDB API</b> + <b style='color:#a0aec0'>AWS</b><br><br>
    Pipeline: Lambda → S3 → Athena<br>
    Updated daily at 9:00 PM IST
    </div>
    """, unsafe_allow_html=True)

# ── HEADER ──
st.title("🎬 Project Insights")
st.markdown("<p class='caption-text'>Real-time movie trend analytics · Data collected daily since Feb 20, 2026</p>", unsafe_allow_html=True)
st.markdown("---")

# ── STAT CARDS ──
total = run_query("SELECT COUNT(DISTINCT id) as total FROM project_insights.daily_metrics")
top_movie = run_query("""
    SELECT m.title, m.release_year, d.popularity 
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.popularity DESC LIMIT 1
""")
latest_date = run_query("SELECT MAX(snapshot_date) as dt FROM project_insights.daily_metrics")
days = run_query("SELECT COUNT(DISTINCT snapshot_date) as days FROM project_insights.daily_metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("🎥 Total Movies Tracked", f"{total['total'][0]:,}")
col2.metric("🔥 Most Popular Today", 
    f"{top_movie['title'][0]} ({top_movie['release_year'][0]})", 
    f"Score: {top_movie['popularity'][0]:.1f}")
col3.metric("📅 Latest Snapshot", latest_date['dt'][0])
col4.metric("📆 Days of Data", f"{days['days'][0]} days")

st.markdown("---")

# ── TOP 10 POPULAR ──
st.subheader("🔥 Top 10 Most Popular Movies Today")

top10 = run_query("""
    SELECT m.title, m.release_year, d.popularity, d.vote_average, d.vote_count,
           CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.popularity DESC
    LIMIT 10
""")

fig = px.bar(
    top10, x="popularity", y="display_title",
    orientation="h",
    color="popularity",
    color_continuous_scale="Blues",
    labels={"popularity": "Popularity Score", "display_title": "Movie"},
    hover_data={"vote_average": ":.2f", "vote_count": ":,", "display_title": False}
)
fig.update_layout(
    yaxis=dict(autorange="reversed"),
    height=420,
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    xaxis=dict(gridcolor="#2d3748"),
    yaxis2=dict(gridcolor="#2d3748"),
    coloraxis_colorbar=dict(title="Score")
)
fig.update_coloraxes(colorbar_tickfont_color="#e2e8f0")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── TREND EXPLORER ──
st.subheader("📈 Trend Explorer")
st.caption("Search a movie to see how its popularity and rating changed over time")

search = st.text_input("🔍 Search movie title", placeholder="e.g. Tenet, Inception, Dune...")

if search:
    movie_list = run_query(f"""
        SELECT DISTINCT m.id, m.title, m.release_year,
               CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
        FROM project_insights.movies_master m
        WHERE LOWER(m.title) LIKE LOWER('%{search}%')
        ORDER BY m.release_year DESC
        LIMIT 15
    """)

    if movie_list.empty:
        st.warning("No movies found. Try a different search term.")
    else:
        selected_display = st.selectbox(
            "Select a movie",
            movie_list['display_title'].tolist()
        )
        movie_row = movie_list[movie_list['display_title'] == selected_display].iloc[0]
        movie_id = movie_row['id']

        trend = run_query(f"""
            SELECT snapshot_date, popularity, vote_average, vote_count
            FROM project_insights.daily_metrics
            WHERE id = {movie_id}
            ORDER BY snapshot_date
        """)

        trend['snapshot_date'] = trend['snapshot_date'].astype(str)
        trend = trend.rename(columns={"vote_average": "rating"})

        col1, col2 = st.columns(2)

        with col1:
            fig2 = px.line(
                trend, x="snapshot_date", y="popularity",
                title=f"Popularity Trend — {selected_display}",
                markers=True,
                color_discrete_sequence=["#63b3ed"]
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="#2d3748", title="Date"),
                yaxis=dict(gridcolor="#2d3748", title="Popularity Score"),
                title_font_color="#ffffff"
            )
            fig2.update_traces(line=dict(width=2.5), marker=dict(size=7))
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            fig3 = px.line(
                trend, x="snapshot_date", y="rating",
                title=f"Rating Trend — {selected_display}",
                markers=True,
                color_discrete_sequence=["#f6ad55"]
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="#2d3748", title="Date"),
                yaxis=dict(gridcolor="#2d3748", title="Rating (out of 10)"),
                title_font_color="#ffffff"
            )
            fig3.update_traces(line=dict(width=2.5), marker=dict(size=7))
            st.plotly_chart(fig3, use_container_width=True)

        # Vote count below
        fig4 = px.bar(
            trend, x="snapshot_date", y="vote_count",
            title=f"Vote Count Growth — {selected_display}",
            color_discrete_sequence=["#68d391"]
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            xaxis=dict(gridcolor="#2d3748", title="Date"),
            yaxis=dict(gridcolor="#2d3748", title="Total Votes"),
            title_font_color="#ffffff",
            height=300
        )
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

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

fig5 = px.bar(
    by_year, x="release_year", y="avg_popularity",
    color="avg_popularity",
    color_continuous_scale="Blues",
    labels={"release_year": "Release Year", "avg_popularity": "Avg Popularity"},
    text="movie_count"
)
fig5.update_traces(texttemplate='%{text} movies', textposition='outside')
fig5.update_layout(
    height=420, showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    xaxis=dict(gridcolor="#2d3748", dtick=1),
    yaxis=dict(gridcolor="#2d3748")
)
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ── GENRE CHART ──
st.subheader("🎭 Average Rating by Genre")

genre_data = run_query("""
    SELECT m.genre_ids, AVG(d.vote_average) as avg_rating, COUNT(DISTINCT d.id) as movie_count
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    AND m.genre_ids IS NOT NULL
    GROUP BY m.genre_ids
""")

# Map genre IDs to primary genre name
genre_data['primary_genre'] = genre_data['genre_ids'].apply(parse_genre)
genre_agg = genre_data.groupby('primary_genre').agg(
    avg_rating=('avg_rating', 'mean'),
    movie_count=('movie_count', 'sum')
).reset_index()
genre_agg = genre_agg[genre_agg['primary_genre'] != 'Other'].sort_values('avg_rating', ascending=True)
genre_agg['avg_rating'] = genre_agg['avg_rating'].round(2)

fig6 = px.bar(
    genre_agg, x="avg_rating", y="primary_genre",
    orientation="h",
    color="avg_rating",
    color_continuous_scale="Oranges",
    labels={"avg_rating": "Avg Rating", "primary_genre": "Genre"},
    text="avg_rating"
)
fig6.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig6.update_layout(
    height=500, showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    xaxis=dict(gridcolor="#2d3748", range=[0, 10]),
    yaxis=dict(gridcolor="#2d3748")
)
st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── LANGUAGE DISTRIBUTION ──
st.subheader("🌍 Movies by Original Language")

lang_data = run_query("""
    SELECT m.original_language, COUNT(DISTINCT m.id) as movie_count
    FROM project_insights.movies_master m
    GROUP BY m.original_language
    ORDER BY movie_count DESC
    LIMIT 10
""")

LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'ko': 'Korean', 'ja': 'Japanese',
    'fr': 'French', 'es': 'Spanish', 'zh': 'Chinese', 'it': 'Italian',
    'de': 'German', 'pt': 'Portuguese', 'tr': 'Turkish', 'th': 'Thai',
    'ru': 'Russian', 'ar': 'Arabic', 'ta': 'Tamil', 'te': 'Telugu'
}
lang_data['language'] = lang_data['original_language'].map(lambda x: LANG_MAP.get(x, x.upper()))

fig7 = px.pie(
    lang_data, values="movie_count", names="language",
    color_discrete_sequence=px.colors.qualitative.Set3,
    hole=0.4
)
fig7.update_layout(
    height=450,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    legend=dict(font=dict(color="#e2e8f0"))
)
fig7.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

# ── TOP 10 MOST VOTED ──
st.subheader("⭐ Top 10 Most Voted Movies")

top_voted = run_query("""
    SELECT m.title, m.release_year, d.vote_count, d.vote_average,
           CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
    FROM project_insights.daily_metrics d
    JOIN project_insights.movies_master m ON d.id = m.id
    WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM project_insights.daily_metrics)
    ORDER BY d.vote_count DESC
    LIMIT 10
""")
top_voted = top_voted.rename(columns={"vote_average": "rating"})

fig8 = px.bar(
    top_voted, x="vote_count", y="display_title",
    orientation="h",
    color="rating",
    color_continuous_scale="RdYlGn",
    labels={"vote_count": "Total Votes", "display_title": "Movie", "rating": "Rating"},
    text="rating"
)
fig8.update_traces(texttemplate='⭐ %{text:.1f}', textposition='outside')
fig8.update_layout(
    yaxis=dict(autorange="reversed"),
    height=420, showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0"),
    xaxis=dict(gridcolor="#2d3748"),
    yaxis2=dict(gridcolor="#2d3748")
)
st.plotly_chart(fig8, use_container_width=True)

# ── FOOTER ──
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #4a5568; font-size: 12px; padding: 8px 0;'>
Project Insights · Sem 6 Mini Project · Data sourced from TMDB API · Powered by AWS Lambda + S3 + Athena
</div>
""", unsafe_allow_html=True)