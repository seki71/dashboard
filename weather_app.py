import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


st.set_page_config(layout="wide")

# ======================================================
# 🎨 STYLING
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
</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================

st.sidebar.markdown("## ⚙️ Controls")

module = st.sidebar.radio(
    "Module",
    ["🌍 Wereldkaart", "📍 Weather Forecast", "🔬 NL Energie Onderzoek"]
)

selected_year = st.sidebar.selectbox(
    "Jaar (NL onderzoek)",
    [2019, 2020, 2021, 2022, 2023]
)

if st.sidebar.button("🔄 Refresh Wereldkaart"):
    st.cache_data.clear()

# ======================================================
# 🌍 WERELDKAART
# ======================================================

if module == "🌍 Wereldkaart":

    st.header("🌍 Wereld Temperatuur Analyse")

    cities = {
        "Amsterdam": (52.37,4.90,"Europe"),
        "Rotterdam": (51.92,4.48,"Europe"),
        "London": (51.50,-0.12,"Europe"),
        "Paris": (48.85,2.35,"Europe"),
        "Berlin": (52.52,13.40,"Europe"),
        "Madrid": (40.42,-3.70,"Europe"),
        "New York": (40.71,-74.00,"North America"),
        "Los Angeles": (34.05,-118.24,"North America"),
        "Toronto": (43.65,-79.38,"North America"),
        "Rio de Janeiro": (-22.90,-43.20,"South America"),
        "Tokyo": (35.68,139.69,"Asia"),
        "Singapore": (1.29,103.85,"Asia"),
        "Dubai": (25.20,55.27,"Asia"),
        "Sydney": (-33.86,151.21,"Oceania"),
        "Cape Town": (-33.92,18.42,"Africa")
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
                "continent": list(cities.values())[i][2],
                "lat": list(cities.values())[i][0],
                "lon": list(cities.values())[i][1],
                "temp": response[i]["current_weather"]["temperature"],
                "wind": response[i]["current_weather"]["windspeed"]
            })
        return pd.DataFrame(data)

    df = get_world()

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Gem. Temp", f"{df['temp'].mean():.1f} °C")
    col2.metric("Warmste stad", df.sort_values("temp",ascending=False).iloc[0]["city"])
    col3.metric("Gem. Wind", f"{df['wind'].mean():.1f} km/h")

    # Fix negatieve size
    df["size_temp"] = df["temp"].abs() + 5

    # Wereldkaart
    fig_map = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="temp",
        size="size_temp",
        hover_name="city",
        projection="natural earth",
        color_continuous_scale="Turbo",
        template="plotly_dark",
        title="Live Wereldtemperaturen"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Extra grafieken
    col1, col2 = st.columns(2)

    with col1:
        fig_rank = px.bar(
            df.sort_values("temp",ascending=False),
            x="city",
            y="temp",
            template="plotly_dark",
            title="Temperatuur ranking"
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with col2:
        fig_wind = px.bar(
            df.sort_values("wind",ascending=False),
            x="city",
            y="wind",
            template="plotly_dark",
            title="Wind ranking"
        )
        st.plotly_chart(fig_wind, use_container_width=True)
# ======================================================
# 📍 WEATHER FORECAST + VERGELIJKING + 1 STAD ANALYSE
# ======================================================

if module == "📍 Weather Forecast":

    st.header("📍 7-daagse Forecast")

    coords = {
        "Amsterdam": (52.37,4.90),
        "London": (51.50,-0.12),
        "New York": (40.71,-74.00),
        "Tokyo": (35.68,139.69),
        "Sydney": (-33.86,151.21)
    }

    # ---------------------------
    # 1️⃣ VERGELIJKING 2 STEDEN
    # ---------------------------

    st.subheader("🔄 Vergelijk 2 steden")

    col1, col2 = st.columns(2)
    city1 = col1.selectbox("Stad 1", list(coords.keys()))
    city2 = col2.selectbox("Stad 2", list(coords.keys()), index=1)

    def get_forecast(city):
        lat, lon = coords[city]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        data = requests.get(url).json()
        return pd.DataFrame({
            "date": data["daily"]["time"],
            "max_temp": data["daily"]["temperature_2m_max"],
            "min_temp": data["daily"]["temperature_2m_min"],
            "rain": data["daily"]["precipitation_sum"]
        })

    df1 = get_forecast(city1)
    df2 = get_forecast(city2)

    fig_compare = go.Figure()
    fig_compare.add_trace(go.Scatter(x=df1["date"], y=df1["max_temp"], mode="lines+markers", name=f"{city1} Max"))
    fig_compare.add_trace(go.Scatter(x=df2["date"], y=df2["max_temp"], mode="lines+markers", name=f"{city2} Max"))
    fig_compare.update_layout(template="plotly_dark", title="Max temperatuur vergelijking")
    st.plotly_chart(fig_compare, use_container_width=True)

    # ---------------------------
    # 2️⃣ VOLLEDIGE ANALYSE 1 STAD
    # ---------------------------

    st.markdown("---")
    st.subheader("📊 Diepgaande analyse van 1 stad")

    single_city = st.selectbox("Kies stad voor volledige analyse", list(coords.keys()))

    df_single = get_forecast(single_city)

    col1, col2, col3 = st.columns(3)
    col1.metric("Gem. Max", f"{df_single['max_temp'].mean():.1f} °C")
    col2.metric("Gem. Min", f"{df_single['min_temp'].mean():.1f} °C")
    col3.metric("Totale regen", f"{df_single['rain'].sum():.1f} mm")

    fig_temp = px.line(
        df_single,
        x="date",
        y=["max_temp","min_temp"],
        template="plotly_dark",
        title=f"Temperatuurverloop - {single_city}"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    fig_rain = px.bar(
        df_single,
        x="date",
        y="rain",
        template="plotly_dark",
        title="Neerslag per dag"
    )
    st.plotly_chart(fig_rain, use_container_width=True)

# ======================================================
# 🔬 NL ENERGIE ONDERZOEK
# ======================================================

if module == "🔬 NL Energie Onderzoek":

    st.header("🔬 Temperatuur vs Elektriciteitsverbruik (Nederland)")

    # =============================
    # DATA OPHALEN
    # =============================

    @st.cache_data(ttl=86400)
    def get_temp():
        url = (
            "https://archive-api.open-meteo.com/v1/archive?"
            "latitude=52.37&longitude=4.90"
            "&start_date=2019-01-01"
            "&end_date=2023-12-31"
            "&daily=temperature_2m_mean"
        )
        response = requests.get(url).json()

        df = pd.DataFrame({
            "date": response["daily"]["time"],
            "temp": response["daily"]["temperature_2m_mean"]
        })

        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        monthly = df.groupby(["year", "month"])["temp"].mean().reset_index()
        return monthly

    @st.cache_data(ttl=86400)
    def get_cbs():
        url = "https://opendata.cbs.nl/ODataApi/odata/84575NED/TypedDataSet"
        df = pd.DataFrame(requests.get(url).json()["value"])

        df = df[df["Perioden"].str.contains("2019|2020|2021|2022|2023")]
        df = df[df["Perioden"].str.contains("M")]

        df_energy = df[["Perioden", "NettoVerbruikBerekend_30"]]
        df_energy.columns = ["period", "electricity"]

        df_energy["year"] = df_energy["period"].str[:4].astype(int)
        df_energy["month"] = df_energy["period"].str.extract(r"M(\d+)").astype(int)
        df_energy["electricity"] = df_energy["electricity"] / 1000  # naar GWh

        return df_energy[["year", "month", "electricity"]]

    temp_df = get_temp()
    energy_df = get_cbs()

    merged = pd.merge(temp_df, energy_df, on=["year", "month"])
    df_year = merged[merged["year"] == selected_year]

    x = df_year["temp"]
    y = df_year["electricity"]

    slope, intercept = np.polyfit(x, y, 1)
    regression_line = slope * x + intercept
    r2 = x.corr(y) ** 2

    # =============================
    # SWITCH (bovenin onderzoek)
    # =============================

    view = st.radio(
        "📊 Kies analyse:",
        [
            "📈 Regressie",
            "📊 Maandelijkse Trend",
            "🔥 Correlatiematrix",
            "📉 Residual Plot",
            "📅 Jaarvergelijking"
        ],
        horizontal=True
    )

    st.markdown("---")

    # =============================
    # GRAFIEK LOGICA
    # =============================

    if view == "📈 Regressie":

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="Maanden"
        ))

        fig.add_trace(go.Scatter(
            x=x,
            y=regression_line,
            mode="lines",
            name=f"Regressielijn (R²={r2:.2f})"
        ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Gemiddelde maandtemperatuur (°C)",
            yaxis_title="Elektriciteitsverbruik (GWh)"
        )

        st.plotly_chart(fig, use_container_width=True)

    elif view == "📊 Maandelijkse Trend":

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_year["month"],
            y=df_year["temp"],
            mode="lines+markers",
            name="Temperatuur (°C)"
        ))

        fig.add_trace(go.Scatter(
            x=df_year["month"],
            y=df_year["electricity"],
            mode="lines+markers",
            name="Elektriciteit (GWh)",
            yaxis="y2"
        ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Maand (1=Jan, 12=Dec)",
            yaxis_title="Temperatuur (°C)",
            yaxis2=dict(
                title="Elektriciteitsverbruik (GWh)",
                overlaying="y",
                side="right"
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    elif view == "🔥 Correlatiematrix":

        corr = df_year[["temp", "electricity"]].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale="Turbo"
        ))

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

    elif view == "📉 Residual Plot":

        residuals = y - regression_line

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x,
            y=residuals,
            mode="markers",
            name="Residuals"
        ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Temperatuur (°C)",
            yaxis_title="Residual (model fout)"
        )

        st.plotly_chart(fig, use_container_width=True)

    elif view == "📅 Jaarvergelijking":

        fig = px.line(
            merged,
            x="month",
            y="electricity",
            color="year",
            template="plotly_dark",
            title="Elektriciteitsverbruik per maand (2019-2023)"
        )

        st.plotly_chart(fig, use_container_width=True)

    # =============================
    # AUTOMATISCHE CONCLUSIE
    # =============================

    st.markdown("---")
    st.subheader("🧠 Automatische Conclusie")

    direction = "negatieve" if slope < 0 else "positieve"

    st.write(f"""
In {selected_year} zien we een **{direction} relatie** tussen temperatuur en elektriciteitsverbruik.

R² = **{r2:.2f}**

→ Ongeveer **{r2*100:.1f}%** van de variatie in elektriciteitsverbruik wordt verklaard door temperatuur.
""")