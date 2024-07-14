from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from swb_meter.db import get_db


def get_data():
    query = """
    SELECT t.created_at, t.temperature, t.humidity,
        t.battery, t.rssi, t.mac_address, coalesce(m.alias, "no alias") as alias
    FROM Temperature as t
    LEFT JOIN Meter as m using(mac_address)
    """
    conn = get_db().conn
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["created_at"] = pd.to_datetime(df["created_at"])  # convert to datetime

    return df


def get_start_time(df, time_range: str):
    latest_created_at = df["created_at"].max()  # latest

    if time_range == "1 Hour":
        start_time = latest_created_at - timedelta(hours=1)
    elif time_range == "1 Day":
        start_time = latest_created_at - timedelta(days=1)
    elif time_range == "1 Week":
        start_time = latest_created_at - timedelta(weeks=1)
    elif time_range == "1 Month":
        start_time = latest_created_at - timedelta(days=30)
    elif time_range == "1 Year":
        start_time = latest_created_at - timedelta(days=365)

    return [start_time, latest_created_at]


# fetch data
df = get_data()
aliases = df["alias"].unique()  # aliases for meter devices


# states
selected_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["1 Hour", "1 Day", "1 Week", "1 Month", "1 Year"],
    index=0,
)
selected_aliases = st.sidebar.multiselect("Select alias", aliases, default=aliases)

# drived state
derived_time_range = get_start_time(df, selected_range)
derived_df = df[df["alias"].isin(selected_aliases)]


# ui -------------------------------------
st.title("SwitchBot Meter Dashboard")


# for calculating metrics, we need to get the latest data and the previous data
latest_data = derived_df.groupby("alias").last()
previous_data = derived_df.groupby("alias").nth(-2).set_index("alias")

# display latest metrics
st.header("Latest Metrics")

metrics = ["temperature", "humidity"]  # , "battery", "rssi"]
for alias in selected_aliases:
    col1, col2, col3 = st.columns([1, 1, 1], gap="large", vertical_alignment="center")

    latest = latest_data.loc[alias]
    previous = previous_data.loc[alias]

    col1.subheader(alias)
    col1.text(latest["created_at"])

    col2.metric(
        label="Temperature",
        value=f"{latest['temperature']:.1f}℃",
        delta=f"{latest['temperature'] - previous['temperature']:.1f}℃",
        delta_color="off",
    )
    col3.metric(
        label="Humidity",
        value=f"{latest['humidity']:.1f}%",
        delta=f"{latest['humidity'] - previous['humidity']:.1f}%",
        delta_color="off",
    )


st.header("Time Series")

line_kwargs = {
    "labels": {"created_at": ""},
    "markers": True,
    "range_x": derived_time_range,
}

fig = px.line(
    derived_df,
    x="created_at",
    y="temperature",
    color="alias",
    title="Temperature",
    **line_kwargs,
)
st.plotly_chart(fig)

fig = px.line(
    derived_df,
    x="created_at",
    y="humidity",
    color="alias",
    title="Humidity",
    **line_kwargs,
)
st.plotly_chart(fig)

fig = px.line(
    derived_df,
    x="created_at",
    y="battery",
    color="alias",
    title="Battery",
    **line_kwargs,
)
st.plotly_chart(fig)

fig = px.line(
    derived_df,
    x="created_at",
    y="rssi",
    color="alias",
    title="RSSI",
    **line_kwargs,
)
st.plotly_chart(fig)
