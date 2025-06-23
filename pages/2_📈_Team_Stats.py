import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from leagueManager import LeagueManager
from sklearn.preprocessing import MinMaxScaler
import subprocess

STAT_ORDER = ['R', 'HR', 'RBI', 'OBP', 'SB', 'K', 'W', 'SV', 'ERA', 'WHIP']
ASCENDING_STATS = {'ERA', 'WHIP'}  
FLOAT_COLS = {'ERA', 'WHIP', 'OBP'}
FORMAT_DICT = {col: "{:.3f}" if col in FLOAT_COLS else "{:.0f}" for col in STAT_ORDER}


# --- Refresh Button ---
if st.button("🔄 Refresh Stats"):
    with st.spinner("Refreshing stats..."):
        result = subprocess.run(["python", "getStats.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ Stats refreshed successfully!")
        else:
            st.error("❌ Failed to refresh stats.")
            st.text(result.stderr)


# --- Load Stats ---
@st.cache_data
def load_team_stats():
    with open("team_stats.json") as f:
        return json.load(f)

team_stats = load_team_stats()
df = pd.DataFrame.from_dict(team_stats, orient="index")
df.index.name = "Team"
df = df[STAT_ORDER]
df_stats = df.copy()

# --- Styled Table ---
st.title("📈 Accumulated Team Stats")
st.dataframe(df.style.format(FORMAT_DICT), use_container_width=True)

# --- Logos ---
manager = LeagueManager(league_id=121531, year=2025)
league = manager.get_league()
logo_map = {team.team_name: team.logo_url for team in league.teams}

# --- Bar Chart ---
st.title("📊 Team Performance Charts")
selected_stat = st.selectbox("Choose a Stat to Compare", STAT_ORDER)
ascending = selected_stat in ASCENDING_STATS
df_sorted = df_stats.sort_values(by=selected_stat, ascending=ascending)

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(df_sorted.index, df_sorted[selected_stat], color='lightcoral')
ax.set_title(f"{selected_stat} by Team")
ax.set_xlabel("Team")
ax.set_ylabel(selected_stat)
plt.xticks(rotation=45)

for bar in bars:
    height = bar.get_height()
    label = FORMAT_DICT[selected_stat].format(height)
    offset = (df_sorted[selected_stat].max() - df_sorted[selected_stat].min()) * 0.01 or 0.1
    ax.text(bar.get_x() + bar.get_width() / 2, height + offset, label, ha='center', va='bottom')

st.pyplot(fig)

# --- Line Chart ---
selected_stat = st.selectbox("Choose a Stat to Plot Over Teams", STAT_ORDER, key="linechart")
ascending = selected_stat in ASCENDING_STATS
df_sorted = df_stats.sort_values(by=selected_stat, ascending=ascending)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df_sorted.index, df_sorted[selected_stat], marker='o', linestyle='-')
ax.set_title(f"{selected_stat} by Team")
ax.set_xlabel("Team")
ax.set_ylabel(selected_stat)
plt.xticks(rotation=45)
st.pyplot(fig)

# --- Radar Line Chart ---
scaler = MinMaxScaler()
df_normalized = pd.DataFrame(
    scaler.fit_transform(df_stats),
    columns=df_stats.columns,
    index=df_stats.index
)
df_melt = df_normalized.reset_index().melt(id_vars='Team', var_name='Stat', value_name='Value')

fig_all = px.line(
    df_melt,
    x='Stat',
    y='Value',
    color='Team',
    line_group='Team',
    markers=True,
    title='Normalized Stat Comparison Across Teams'
)
st.plotly_chart(fig_all)
