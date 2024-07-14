import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from swb_meter.db import datetime_to_str, get_db, str_to_datetime


def get_data_in_range(from_time: str, to_time: str):
    """Get data from the database.

    by default, from_time is set to an empty string,
    which means it will get all the data which has some value in the created_at column.

    use this function to get the latest data by setting from_time to the last ingested time.
    """

    query = """
    SELECT t.created_at, t.temperature, t.humidity,
        t.battery, t.rssi, t.mac_address, coalesce(m.alias, "no alias") as alias
    FROM Temperature as t
    LEFT JOIN Meter as m using(mac_address)
    WHERE ? < t.created_at AND t.created_at <= ?
    """
    conn = get_db().conn
    df = pd.read_sql_query(query, conn, params=(from_time, to_time))
    conn.close()

    df["created_at"] = pd.to_datetime(df["created_at"])  # convert to datetime

    return df


def get_chart_time_range(end_time: datetime, time_range: str):
    if time_range == "1 Hour":
        start_time = end_time - timedelta(hours=1)
    elif time_range == "1 Day":
        start_time = end_time - timedelta(days=1)
    elif time_range == "1 Week":
        start_time = end_time - timedelta(weeks=1)
    elif time_range == "1 Month":
        start_time = end_time - timedelta(days=30)
    elif time_range == "1 Year":
        start_time = end_time - timedelta(days=365)

    return [start_time, end_time]


# states
if "refreshed_at" not in st.session_state:
    st.session_state["refreshed_at"] = datetime_to_str(datetime.now())

refreshed_at = st.session_state.refreshed_at


if "df" not in st.session_state:
    # all data until now
    st.session_state["df"] = get_data_in_range("", refreshed_at)

df = st.session_state.df

refresh = st.sidebar.toggle("Auto Refresh Data", False)
selected_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["1 Hour", "1 Day", "1 Week", "1 Month", "1 Year"],
    index=0,
)

aliases = df["alias"].unique()  # aliases for meter devices
selected_aliases = st.sidebar.multiselect(
    "Select alias", aliases, default=aliases, key="aliases"
)


# derived from states
derived_time_range = get_chart_time_range(str_to_datetime(refreshed_at), selected_range)
derived_df = df[df["alias"].isin(selected_aliases)]
aliases = df["alias"].unique()  # aliases for meter devices

# ui -------------------------------------
st.title("SwitchBot Meter Dashboard")
st.write(f"Last refreshed at: {refreshed_at}")

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


# refresh data
while refresh:
    now = datetime_to_str(datetime.now())
    new_df = get_data_in_range(refreshed_at, now)

    if new_df.empty:
        time.sleep(10)  # polling interval for new data
        continue

    st.session_state.refreshed_at = now
    st.session_state.df = pd.concat([df, new_df])

    st.rerun()  # refresh the page when new data is available
