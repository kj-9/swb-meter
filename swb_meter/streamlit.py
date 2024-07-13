from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from swb_meter.db import get_db

# SQLiteデータベースに接続
conn = get_db().conn

# データを読み込む
query = """
SELECT t.created_at, t.temperature, t.humidity,
       t.battery, t.rssi, t.mac_address, coalesce(m.alias, "no alias") as alias
FROM Temperature as t
LEFT JOIN Meter as m using(mac_address)
"""
df = pd.read_sql_query(query, conn)
df["created_at"] = pd.to_datetime(df["created_at"])  # タイムスタンプをdatetime型に変換


# 最新のデータの日時
latest_created_at = df["created_at"].max()

# タイムレンジの選択
time_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["1 Hour", "1 Day", "1 Week", "1 Month", "1 Year"],
    index=0,
)


# タイムレンジに基づいてデータをフィルタリング
if time_range == "1 Hour":
    start_time = latest_created_at - timedelta(hours=1)
elif time_range == "1 Day":
    start_time = latest_created_at - timedelta(days=1)
elif time_range == "1 Week":
    start_time = latest_created_at - timedelta(weeks=1)
elif time_range == "1 Month":
    start_time = latest_created_at - timedelta(
        days=30
    )  # 精確な月の日数を計算する場合は、他の方法を検討してください
elif time_range == "1 Year":
    start_time = latest_created_at - timedelta(days=365)


st.title("SwitchBot Meter Data Dashboard")

# alias
aliases = df["alias"].unique()
selected_aliases = st.sidebar.multiselect("Select alias", aliases, default=aliases)


# フィルタリングされたデータフレーム
filtered_df = df[df["alias"].isin(selected_aliases)]


# aliasごとに最新のデータを表示
# 前回のデータを取得（2番目に新しいデータ）
latest_data = filtered_df.groupby("alias").last()
previous_data = filtered_df.groupby("alias").nth(-2).set_index("alias")

# aliasごとに最新のデータをメトリクスで表示（差分付き）
st.header("Latest Metrics")

metrics = ["temperature", "humidity"]  # , "バッテリー", "RSSI"]
for alias in selected_aliases:
    col1, col2, col3 = st.columns([1, 1, 1], gap="large", vertical_alignment="center")

    latest = latest_data.loc[alias]
    previous = previous_data.loc[alias]

    col1.subheader(alias)
    col1.text(latest["created_at"])

    col2.metric(
        label="温度",
        value=f"{latest['temperature']:.1f}℃",
        delta=f"{latest['temperature'] - previous['temperature']:.1f}℃",
    )
    col3.metric(
        label="湿度",
        value=f"{latest['humidity']:.1f}%",
        delta=f"{latest['humidity'] - previous['humidity']:.1f}%",
    )


st.header("Time Series")

labels = {"created_at": ""}

# 温度の時系列グラフ（2つのセンサーを1つのグラフに）
fig = px.line(
    filtered_df,
    x="created_at",
    y="temperature",
    color="alias",
    title="Temperature",
    labels=labels,
    markers=True,
    range_x=[start_time, latest_created_at],
)
st.plotly_chart(fig)

# 湿度の時系列グラフ（2つのセンサーを1つのグラフに）
fig = px.line(
    filtered_df,
    x="created_at",
    y="humidity",
    color="alias",
    title="Humidity",
    labels=labels,
)
st.plotly_chart(fig)

# バッテリー残量の時系列グラフ（2つのセンサーを1つのグラフに）
fig = px.line(
    filtered_df,
    x="created_at",
    y="battery",
    color="alias",
    title="Battery",
    labels=labels,
)
st.plotly_chart(fig)

# RSSIの時系列グラフ（2つのセンサーを1つのグラフに）
fig = px.line(
    filtered_df, x="created_at", y="rssi", color="alias", title="RSSI", labels=labels
)
st.plotly_chart(fig)

# 接続を閉じる
conn.close()
