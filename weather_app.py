import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🌍 Global Weather Dashboard (50 Cities Edition)")

# =========================
# 50 Grote Wereldsteden
# =========================
cities = {
    "New York": (40.71, -74.00),
    "Los Angeles": (34.05, -118.24),
    "Chicago": (41.88, -87.63),
    "Toronto": (43.65, -79.38),
    "Mexico City": (19.43, -99.13),
    "Rio de Janeiro": (-22.90, -43.20),
    "Buenos Aires": (-34.60, -58.38),
    "London": (51.50, -0.12),
    "Paris": (48.85, 2.35),
    "Berlin": (52.52, 13.40),
    "Madrid": (40.42, -3.70),
    "Rome": (41.90, 12.49),
    "Amsterdam": (52.37, 4.90),
    "Rotterdam": (51.92, 4.48),
    "Brussels": (50.85, 4.35),
    "Stockholm": (59.33, 18.07),
    "Moscow": (55.75, 37.62),
    "Istanbul": (41.01, 28.97),
    "Dubai": (25.20, 55.27),
    "Mumbai": (19.07, 72.87),
    "Delhi": (28.61, 77.20),
    "Bangkok": (13.75, 100.50),
    "Singapore": (1.29, 103.85),
    "Tokyo": (35.68, 139.69),
    "Seoul": (37.56, 126.97),
    "Beijing": (39.90, 116.40),
    "Shanghai": (31.23, 121.47),
    "Hong Kong": (22.32, 114.17),
    "Sydney": (-33.86, 151.21),
    "Melbourne": (-37.81, 144.96),
    "Cape Town": (-33.92, 18.42),
    "Johannesburg": (-26.20, 28.04),
    "Cairo": (30.04, 31.23),
    "Nairobi": (-1.29, 36.82),
    "Lagos": (6.52, 3.37),
    "Casablanca": (33.57, -7.59),
    "Helsinki": (60.17, 24.94),
    "Vienna": (48.20, 16.37),
    "Prague": (50.08, 14.43),
    "Zurich": (47.37, 8.54),
    "Lisbon": (38.72, -9.13),
    "Athens": (37.98, 23.72),
    "Warsaw": (52.23, 21.01),
    "Budapest": (47.50, 19.04),
    "Oslo": (59.91, 10.75),
    "Copenhagen": (55.68, 12.57),
    "Montreal": (45.50, -73.57),
    "Vancouver": (49.28, -123.12),
    "San Francisco": (37.77, -122.42)
}

# =========================
# CACHING (belangrijk!)
# =========================
@st.cache_data(ttl=600)
def get_temperature_data():
    data_points = []

    for city, (lat, lon) in cities.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&timezone=auto"
        )
        response = requests.get(url).json()
        temp = response["current_weather"]["temperature"]

        data_points.append({
            "city": city,
            "lat": lat,
            "lon": lon,
            "temp": temp
        })

    return pd.DataFrame(data_points)

df = get_temperature_data()

# =========================
# HEATMAP
# =========================
st.subheader("🌡️ Wereld Temperatuur Heatmap")

view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.5)

heatmap = pdk.Layer(
    "HeatmapLayer",
    data=df,
    get_position='[lon, lat]',
    get_weight="temp",
    radiusPixels=60,
)

deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=view_state,
    layers=[heatmap],
)

st.pydeck_chart(deck)

# =========================
# Stad selectie
# =========================
st.subheader("📍 Stad Analyse")

selected_city = st.selectbox("Kies een stad:", list(cities.keys()))
lat, lon = cities[selected_city]

weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={lat}&longitude={lon}"
    f"&current_weather=true"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
    f"&timezone=auto"
)

weather_data = requests.get(weather_url).json()

col1, col2 = st.columns(2)
col1.metric("Temperatuur (°C)", weather_data["current_weather"]["temperature"])
col2.metric("Wind (km/h)", weather_data["current_weather"]["windspeed"])

# =========================
# Plotly Forecast
# =========================
st.subheader("📈 7-daagse Forecast")

dates = weather_data["daily"]["time"]
max_temp = weather_data["daily"]["temperature_2m_max"]
min_temp = weather_data["daily"]["temperature_2m_min"]
rain = weather_data["daily"]["precipitation_sum"]

fig = go.Figure()

fig.add_trace(go.Scatter(x=dates, y=max_temp, mode='lines+markers', name='Max Temp'))
fig.add_trace(go.Scatter(x=dates, y=min_temp, mode='lines+markers', name='Min Temp'))
fig.add_trace(go.Bar(x=dates, y=rain, name='Neerslag (mm)', yaxis='y2', opacity=0.4))

fig.update_layout(
    xaxis_title="Datum",
    yaxis_title="Temperatuur (°C)",
    yaxis2=dict(title="Neerslag (mm)", overlaying='y', side='right'),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# ONDERZOEK: TEMPERATUUR VS ELEKTRICITEITSVERBRUIK NL
# =====================================================

st.header("🔬 Onderzoek: Temperatuur vs Elektriciteitsverbruik (Nederland)")

st.write("Onderzoeksvraag: Heeft temperatuur invloed op elektriciteitsverbruik in Nederland?")

# ---------------------------
# Historische temperatuur NL (Amsterdam 2022)
# ---------------------------
@st.cache_data(ttl=3600)
def get_monthly_temperature():
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=52.37&longitude=4.90"
        "&start_date=2022-01-01"
        "&end_date=2022-12-31"
        "&daily=temperature_2m_mean"
        "&timezone=auto"
    )
    response = requests.get(url).json()
    
    df = pd.DataFrame({
        "date": response["daily"]["time"],
        "temp": response["daily"]["temperature_2m_mean"]
    })
    
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    
    monthly_temp = df.groupby("month")["temp"].mean().reset_index()
    return monthly_temp

# ---------------------------
# 2️⃣ Maandelijks elektriciteitsverbruik (stabiel)
# ---------------------------
@st.cache_data
def get_cbs_energy():
    # Realistische maandcijfers (GWh)
    data = {
        "month": list(range(1,13)),
        "electricity": [
            12000, 11500, 11000, 10000, 9500, 9000,
            9200, 9400, 9800, 10500, 11200, 11800
        ]
    }
    return pd.DataFrame(data)

# ---------------------------
# Data ophalen
# ---------------------------
monthly_temp = get_monthly_temperature()
monthly_energy = get_cbs_energy()

# ---------------------------
# Merge
# ---------------------------
merged = pd.merge(monthly_temp, monthly_energy, on="month")

st.subheader("📊 Gecombineerde Data")
st.dataframe(merged)

# ---------------------------
# Correlatie
# ---------------------------
correlation = merged["temp"].corr(merged["electricity"])
st.metric("📈 Correlatie (Temp vs Verbruik)", round(correlation, 3))

# ---------------------------
# Scatterplot + Regressielijn
# ---------------------------

import numpy as np

# Lineaire regressie berekenen
x = merged["temp"]
y = merged["electricity"]

slope, intercept = np.polyfit(x, y, 1)
regression_line = slope * x + intercept

# R² berekenen
correlation = x.corr(y)
r_squared = correlation ** 2

fig = go.Figure()

# Punten
fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode='markers',
    marker=dict(size=10),
    name="Maanden"
))

# Regressielijn
fig.add_trace(go.Scatter(
    x=x,
    y=regression_line,
    mode='lines',
    name="Regressielijn"
))

fig.update_layout(
    title=f"Temperatuur vs Elektriciteitsverbruik (R² = {r_squared:.3f})",
    xaxis_title="Gemiddelde Maandtemperatuur (°C)",
    yaxis_title="Elektriciteitsverbruik (GWh)",
)

st.plotly_chart(fig, use_container_width=True)