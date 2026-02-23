import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Global Weather Dashboard")

# =========================
# Nederlandse + Internationale steden
# =========================
cities = {

    # 🇳🇱 Nederland
    "Amsterdam": (52.37, 4.90),
    "Rotterdam": (51.92, 4.48),
    "Den Haag": (52.08, 4.30),
    "Utrecht": (52.09, 5.12),
    "Eindhoven": (51.44, 5.48),
    "Tilburg": (51.56, 5.09),
    "Groningen": (53.22, 6.57),
    "Almere": (52.35, 5.26),
    "Breda": (51.59, 4.78),
    "Nijmegen": (51.84, 5.86),
    "Enschede": (52.22, 6.89),
    "Haarlem": (52.38, 4.64),
    "Arnhem": (51.98, 5.91),
    "Zwolle": (52.51, 6.09),
    "Leiden": (52.16, 4.49),
    "Maastricht": (50.85, 5.69),
    "Delft": (52.01, 4.36),
    "Alkmaar": (52.63, 4.75),
    "Gouda": (52.01, 4.71),
    "Lelystad": (52.52, 5.47),

    # 🌍 Europa
    "London": (51.50, -0.12),
    "Paris": (48.85, 2.35),
    "Berlin": (52.52, 13.40),
    "Madrid": (40.42, -3.70),
    "Rome": (41.90, 12.49),
    "Vienna": (48.20, 16.37),
    "Prague": (50.08, 14.43),
    "Stockholm": (59.33, 18.07),
    "Warsaw": (52.23, 21.01),
    "Lisbon": (38.72, -9.13),

    # 🌎 Noord-Amerika
    "New York": (40.71, -74.00),
    "Los Angeles": (34.05, -118.24),
    "Chicago": (41.88, -87.63),
    "Toronto": (43.65, -79.38),
    "Vancouver": (49.28, -123.12),
    "Mexico City": (19.43, -99.13),

    # 🌎 Zuid-Amerika
    "Rio de Janeiro": (-22.90, -43.20),
    "Buenos Aires": (-34.60, -58.38),
    "Santiago": (-33.45, -70.66),

    # 🌏 Azië
    "Tokyo": (35.68, 139.69),
    "Seoul": (37.56, 126.97),
    "Beijing": (39.90, 116.40),
    "Shanghai": (31.23, 121.47),
    "Singapore": (1.29, 103.85),
    "Mumbai": (19.07, 72.87),
    "Dubai": (25.20, 55.27),

    # 🌍 Afrika
    "Cape Town": (-33.92, 18.42),
    "Cairo": (30.04, 31.23),
    "Nairobi": (-1.29, 36.82),
    "Lagos": (6.52, 3.37),

    # 🌏 Oceanië
    "Sydney": (-33.86, 151.21),
    "Melbourne": (-37.81, 144.96)
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
# TEMPERATUUR KAART
# =========================
st.subheader("🌡️ Wereld Temperatuur Kaart")

# Temperatuur normaliseren voor kleur
min_temp = df["temp"].min()
max_temp = df["temp"].max()

def temp_to_color(temp):
    ratio = (temp - min_temp) / (max_temp - min_temp + 1e-6)
    red = int(255 * ratio)
    blue = int(255 * (1 - ratio))
    return [red, 0, blue, 200]

df["color"] = df["temp"].apply(temp_to_color)

view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.5)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position='[lon, lat]',
    get_fill_color="color",
    get_radius=200000,
    pickable=True,
)

deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=view_state,
    layers=[layer],
    tooltip={"text": "{city}\nTemp: {temp}°C"}
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
# ONDERZOEK: MEERDERE JAREN TEMPERATUUR VS ENERGIE
# =====================================================

import numpy as np

st.header("🔬 Onderzoek: Temperatuur vs Elektriciteitsverbruik (2019-2023)")

years = [2019, 2020, 2021, 2022, 2023]

# ---------------------------
# Temperatuur ophalen per jaar
# ---------------------------
@st.cache_data(ttl=3600)
def get_monthly_temperature(year):
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=52.37&longitude=4.90"
        f"&start_date={year}-01-01"
        f"&end_date={year}-12-31"
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
    monthly_temp["year"] = year
    return monthly_temp

# ---------------------------
# Simulatie energieverbruik per jaar
# (trend lichte stijging per jaar)
# ---------------------------
def get_energy_for_year(year):
    base = np.array([
        12000,11500,11000,10000,9500,9000,
        9200,9400,9800,10500,11200,11800
    ])
    
    growth = (year - 2019) * 200  # lichte stijging per jaar
    energy = base + growth
    
    df = pd.DataFrame({
        "month": list(range(1,13)),
        "electricity": energy,
        "year": year
    })
    return df

# ---------------------------
# Data verzamelen
# ---------------------------
all_data = []

for year in years:
    temp_df = get_monthly_temperature(year)
    energy_df = get_energy_for_year(year)
    
    merged = pd.merge(temp_df, energy_df, on=["month","year"])
    all_data.append(merged)

full_df = pd.concat(all_data)

st.subheader("📊 Gecombineerde Data")
st.dataframe(full_df.head())

# ---------------------------
# Jaar filter
# ---------------------------
selected_year = st.selectbox("Kies een jaar:", years)

df_year = full_df[full_df["year"] == selected_year]

x = df_year["temp"]
y = df_year["electricity"]

# Regressie berekenen
slope, intercept = np.polyfit(x, y, 1)
regression_line = slope * x + intercept

r_squared = x.corr(y) ** 2

# ---------------------------
# Plot maken
# ---------------------------
fig = go.Figure()

# Punten
fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode='markers',
    marker=dict(size=10),
    name=f"{selected_year} punten"
))

# Regressielijn
fig.add_trace(go.Scatter(
    x=x,
    y=regression_line,
    mode='lines',
    name=f"Regressielijn (R²={r_squared:.2f})"
))

fig.update_layout(
    title=f"Temperatuur vs Elektriciteitsverbruik ({selected_year})",
    xaxis_title="Gemiddelde Maandtemperatuur (°C)",
    yaxis_title="Elektriciteitsverbruik (GWh)",
)

st.plotly_chart(fig, use_container_width=True)