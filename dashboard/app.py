import os, time
import streamlit as st
import pandas as pd
import plotly.express as px
import queries as q

from datetime import datetime, timedelta
project_dir = os.path.join(os.path.dirname(__file__), '..')
clean_path  = os.path.abspath(project_dir)

supabase_client = q.supabase_client
table = 'weather_transformed'
num_unique_city = q.get_distinct_count(supabase_client, table, 'city')

st.set_page_config(
    page_title='Weather Data Engineering Project',
    page_icon=':cloud:',
    layout='wide'
)

st.title(':cloud: Weather Pipeline')
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S+08:00')}")

# Sidebar Filter
st.sidebar.header('Filters')

all_cities = q.get_all_cities(supabase_client, table)

selected_cities = st.sidebar.multiselect(
    label='Select cities',
    options=all_cities,
    default=all_cities
)

date_range = st.sidebar.date_input(
    label='Date range',
    value=[datetime.now() - timedelta(days=1), datetime.now()]
)

st.sidebar.markdown('---')
st.sidebar.caption('Weather Pipeline by Jasper Casile')

auto_refresh = st.sidebar.toggle("Auto-refresh every 5 minutes", value=False)

if auto_refresh:
    import time
    time.sleep(300)
    st.rerun()
    
# Latest readings for each city
latest_df = pd.DataFrame(q.get_latest_readings(supabase_client, table, num_unique_city))

# Checking for selected cities from the filter
if selected_cities: 
    latest_df = latest_df[latest_df['city'].isin(selected_cities)]

col1, col2, col3, col4 = st.columns(4)

with col1:
    hottest = latest_df.loc[latest_df["temp_celsius"].idxmax()]
    st.metric(
        label='Hottest City',
        value=f'{hottest['city']}, {hottest['country']}',
        delta=f"{hottest['temp_celsius']:.1f} °C"
    )

with col2:
    coldest = latest_df.loc[latest_df['temp_celsius'].idxmin()]
    st.metric(
        label='Coldest City',
        value=coldest['city'],
        delta=f"{coldest['temp_celsius']:.1f} °C"
    )

with col3:
    most_humid = latest_df.loc[latest_df['humidity'].idxmax()]
    st.metric(
        label='Most Humid City',
        value=most_humid['city'],
        delta=f"{most_humid['humidity']}%"
    )

with col4:
    avg_temp = latest_df['temp_celsius'].mean()
    st.metric(
        label='Average Temperature',
        value=f'{avg_temp:.1f} °C'
    )

st.markdown('---')

map_fig = px.scatter_geo(
    latest_df,
    lat='lat',
    lon='lon',
    color='temp_celsius',
    size='humidity',
    hover_name='city',
    hover_data={
        'temp_celsius': ':.1f',
        'humidity': True,
        'weather_desc': True,
        'wind_speed': True,
        'lat': True,
        'lon': True
    },
    color_continuous_scale='RdYlBu_r',
    title='Current Temperature by City',
    projection='natural earth'
)

map_fig.update_layout(height=500)
st.plotly_chart(map_fig, width='stretch')

# Line Chart
st.markdown("---")

st.subheader('Temperature History (Last 24 Hours)')

history_df = pd.DataFrame(q.get_temperature_history(supabase_client, table))

# Convert dt_utc to datetime, explicitly handling UTC timezone
history_df['dt_utc'] = pd.to_datetime(history_df['dt_utc'], utc=True)

if selected_cities:
    history_df = history_df[history_df['city'].isin(selected_cities)]

if len(date_range) == 2:
    start_date = pd.Timestamp(date_range[0], tz='UTC')
    end_date   = pd.Timestamp(date_range[1], tz='UTC') + timedelta(days=1)
    history_df = history_df[
        (history_df['dt_utc'] >= start_date) &
        (history_df['dt_utc'] <= end_date)
    ]

# Convert to current timezone
history_df['dt_local'] = history_df['dt_utc'].dt.tz_convert('Asia/Manila')

line_fig = px.line(
    history_df,
    x='dt_local',
    y='temp_celsius',
    color='city',
    markers=True,
    title='Temperature Over Time',
    labels={
        'dt_local': 'Time (UTC+08:00 (Asia/Manila))',
        'temp_celsius': 'Temperature (°C)',
        'city': 'City'
    }
)

line_fig.update_layout(height=400)
st.plotly_chart(line_fig, width='stretch')

st.markdown('---')

col_left, col_right = st.columns(2)

with col_left:
    st.subheader('Humidity Comparison')

    humidity_df = pd.DataFrame(q.get_humidity_comparison(supabase_client, table, num_unique_city))

    if selected_cities:
        humidity_df = humidity_df[humidity_df['city'].isin(selected_cities)]

    bar_fig = px.bar(
        humidity_df,
        x='city',
        y='humidity',
        color='weather_main',
        title='Current Humidity by City',
        labels={
            'city': 'City',
            'humidity': 'Humidity (%)',
            'weather_main': 'Condition'
        }
    )

    bar_fig.update_layout(height=400)
    st.plotly_chart(bar_fig, width='stretch')

with col_right:
    st.subheader('Heat Index Comparison')

    heat_fig = px.bar(
        latest_df.sort_values('heat_index', ascending=False),
        x='city',
        y='heat_index',
        color='temp_celsius',
        color_continuous_scale='RdYlBu_r',
        title='Heat Index by City',
        labels={
            'city': 'City',
            'heat_index': 'Heat Index (°C)',
            'temp_celsius': 'Temp (°C)'
        }
    )

    heat_fig.update_layout(height=400)
    st.plotly_chart(heat_fig, width='stretch')

st.markdown('---')

st.subheader("Latest Readings")

display_cols = [
    "city", "country", "temp_celsius", "feels_like_celsius",
    "humidity", "weather_desc", "wind_speed", "heat_index", "fetched_at"
]

st.dataframe(
    latest_df[display_cols].sort_values("temp_celsius", ascending=False),
    width='stretch',
    hide_index=True
)

st.markdown("---")