import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

# ======================================================
# 🎨 PREMIUM STYLING
# ======================================================

st.markdown("""
<style>
.main { background-color: #0E1117; }
[data-testid="stSidebar"] { background-color: #111827; }
h1, h2, h3 { color: #F9FAFB; }
[data-testid="metric-container"] {
    background-color: #1F2937;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #374151;
}
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Global Weather & Energy Intelligence Dashboard")

# ======================================================
# 🎛 SIDEBAR
# ======================================================

st.sidebar.markdown("## ⚙️ Controls")

module = st.sidebar.radio(
    "Module",
    ["🌍 Wereldkaart", "📍 Stad Analyse", "🔬 NL Energie Onderzoek"]
)

selected_year = st.sidebar.selectbox(
    "Jaar",
    [2019, 2020, 2021, 2022, 2023]
)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()

# ======================================================
# 🌍 WERELDKAART (ANIMATED STYLE)
# ======================================================

if module == "🌍 Wereldkaart":

    cities = {
        "Amsterdam": (52.37,4.90),
        "London": (51.50,-0.12),
        "Paris": (48.85,2.35),
        "Berlin": (52.52,13.40),
        "New York": (40.71,-74.00),
        "Toronto": (43.65,-79.38),
        "Tokyo": (35.68,139.69),
        "Sydney": (-33.86,151.21),
        "Dubai": (25.20,55.27),
        "Singapore": (1.29,103.85)
    }

    @st.cache_data(ttl=3600)
    def get_world():
        lats = ",".join([str(v[0]) for v in cities.values()])
        lons = ",".join([str(v[1]) for v in cities.values()])
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current_weather=true"
        response = requests.get(url).json()

        data = []
        for i, city in enumerate(cities.keys()):
            data.append({
                "city": city,
                "lat": list(cities.values())[i][0],
                "lon": list(cities.values())[i][1],
                "temp": response[i]["current_weather"]["temperature"]
            })
        return pd.DataFrame(data)

    df = get_world()

    col1, col2, col3 = st.columns(3)
    col1.metric("Aantal steden", len(df))
    col2.metric("Gemiddelde temp", f"{df['temp'].mean():.1f}°C")
    col3.metric("Max temp", f"{df['temp'].max():.1f}°C")

    # 🌍 Animated Scatter Map
    fig_map = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="temp",
        size="temp",
        hover_name="city",
        color_continuous_scale="Turbo",
        projection="natural earth"
    )

    fig_map.update_layout(
        template="plotly_dark",
        title="Live Wereldtemperaturen",
        transition_duration=800
    )

    st.plotly_chart(fig_map, use_container_width=True)

# ======================================================
# 📍 STAD ANALYSE (SMOOTH ANIMATED)
# ======================================================

if module == "📍 Stad Analyse":

    city = st.selectbox("Selecteer stad", ["Amsterdam","London","New York","Tokyo","Sydney"])

    coords = {
        "Amsterdam": (52.37,4.90),
        "London": (51.50,-0.12),
        "New York": (40.71,-74.00),
        "Tokyo": (35.68,139.69),
        "Sydney": (-33.86,151.21)
    }

    lat, lon = coords[city]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    data = requests.get(url).json()

    df_city = pd.DataFrame({
        "date": data["daily"]["time"],
        "max": data["daily"]["temperature_2m_max"],
        "min": data["daily"]["temperature_2m_min"]
    })

    fig = px.line(
        df_city,
        x="date",
        y=["max","min"],
        template="plotly_dark",
        title=f"7-daagse Forecast – {city}"
    )

    fig.update_layout(transition_duration=800)

    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 🔬 NL ENERGIE ONDERZOEK (ANIMATED ANALYTICS)
# ======================================================

if module == "🔬 NL Energie Onderzoek":

    st.header("🔬 Temperatuur vs Elektriciteitsverbruik NL")

    nl_cities = {
        "Amsterdam": (52.37,4.90),
        "Rotterdam": (51.92,4.48),
        "Utrecht": (52.09,5.12),
        "Groningen": (53.22,6.57),
        "Eindhoven": (51.44,5.48),
    }

    years = [2019,2020,2021,2022,2023]

    @st.cache_data(ttl=86400)
    def get_temp():
        lats = ",".join([str(v[0]) for v in nl_cities.values()])
        lons = ",".join([str(v[1]) for v in nl_cities.values()])
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lats}&longitude={lons}&start_date=2019-01-01&end_date=2023-12-31&daily=temperature_2m_mean"
        response = requests.get(url).json()

        city_data = []
        for i in range(len(nl_cities)):
            df_temp = pd.DataFrame({
                "date": response[i]["daily"]["time"],
                "temp": response[i]["daily"]["temperature_2m_mean"]
            })
            df_temp["date"] = pd.to_datetime(df_temp["date"])
            df_temp["year"] = df_temp["date"].dt.year
            df_temp["month"] = df_temp["date"].dt.month
            monthly = df_temp.groupby(["year","month"])["temp"].mean().reset_index()
            city_data.append(monthly)

        combined = pd.concat(city_data)
        national = combined.groupby(["year","month"])["temp"].mean().reset_index()
        return national

    @st.cache_data(ttl=86400)
    def get_cbs():
        url = "https://opendata.cbs.nl/ODataApi/odata/84575NED/TypedDataSet"
        df = pd.DataFrame(requests.get(url).json()["value"])
        df = df[df["Perioden"].str.contains("2019|2020|2021|2022|2023")]
        df = df[df["Perioden"].str.contains("M")]
        df_energy = df[["Perioden","NettoVerbruikBerekend_30"]]
        df_energy.columns = ["period","electricity"]
        df_energy["year"] = df_energy["period"].str[:4].astype(int)
        df_energy["month"] = df_energy["period"].str.extract(r"M(\d+)").astype(int)
        return df_energy[["year","month","electricity"]]

    with st.spinner("Data laden..."):
        temp_df = get_temp()
        energy_df = get_cbs()

    merged = pd.merge(temp_df, energy_df, on=["year","month"])
    df_year = merged[merged["year"]==selected_year]

    x = df_year["temp"]
    y = df_year["electricity"]

    slope, intercept = np.polyfit(x,y,1)
    regression_line = slope*x + intercept
    r2 = x.corr(y)**2

    col1, col2, col3 = st.columns(3)
    col1.metric("Gemiddelde Temp", f"{x.mean():.2f}°C")
    col2.metric("Gemiddeld Verbruik", f"{y.mean():,.0f}")
    col3.metric("R²", f"{r2:.3f}")

    fig_reg = go.Figure()
    fig_reg.add_trace(go.Scatter(x=x,y=y,mode="markers",name="Maanden"))
    fig_reg.add_trace(go.Scatter(x=x,y=regression_line,mode="lines",name="Regressie"))

    fig_reg.update_layout(
        template="plotly_dark",
        title=f"Regressie Analyse ({selected_year})",
        xaxis_title="Gemiddelde maandtemperatuur (°C)",
        yaxis_title="Elektriciteitsverbruik",
        transition_duration=800
    )

    st.plotly_chart(fig_reg, use_container_width=True)

    # Animated Trend
    fig_trend = px.line(
        merged,
        x="month",
        y="electricity",
        color="year",
        template="plotly_dark",
        title="Trend Elektriciteitsverbruik 2019-2023"
    )

    fig_trend.update_layout(transition_duration=800)

    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("🧠 Automatische Conclusie")

    direction = "negatieve" if slope < 0 else "positieve"

    st.write(f"""
Er is een **{direction} relatie** tussen temperatuur en elektriciteitsverbruik.
R² = **{r2:.2f}**, wat betekent dat ongeveer **{r2*100:.1f}%**
van de variatie verklaard wordt door temperatuur.
""")