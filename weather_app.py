import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

st.set_page_config(layout="wide")
st.title("🌍 Global Temperature Heatmap Dashboard")

# =========================
# Wereldsteden
# =========================
cities = {
    "New York": (40.71, -74.00),
    "London": (51.50, -0.12),
    "Tokyo": (35.68, 139.69),
    "Sydney": (-33.86, 151.21),
    "Cape Town": (-33.92, 18.42),
    "Rio de Janeiro": (-22.90, -43.20),
    "Dubai": (25.20, 55.27),
    "Mumbai": (19.07, 72.87),
    "Toronto": (43.65, -79.38),
    "Singapore": (1.29, 103.85),
    "Rotterdam": (51.92, 4.48)
}

# =========================
# Temperatuurdata ophalen
# =========================
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

df = pd.DataFrame(data_points)

# =========================
# HEATMAP
# =========================
st.subheader("🌡️ Wereld Temperatuur Heatmap")

view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1.5,
)

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
# Stad selecteren
# =========================
st.subheader("📍 Bekijk details per stad")

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

# =========================
# Huidig weer
# =========================
st.subheader("🌤️ Huidig weer")

col1, col2 = st.columns(2)
col1.metric("Temperatuur (°C)", weather_data["current_weather"]["temperature"])
col2.metric("Wind (km/h)", weather_data["current_weather"]["windspeed"])

# =========================
# Forecast
# =========================
st.subheader("📅 7-daagse voorspelling")

daily_df = pd.DataFrame({
    "Datum": weather_data["daily"]["time"],
    "Max Temp": weather_data["daily"]["temperature_2m_max"],
    "Min Temp": weather_data["daily"]["temperature_2m_min"],
    "Neerslag (mm)": weather_data["daily"]["precipitation_sum"]
})

st.line_chart(daily_df.set_index("Datum"))