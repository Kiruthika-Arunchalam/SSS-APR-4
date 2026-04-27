import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pydeck as pdk
import os

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="SSS Dashboard", layout="wide")

def style_chart(fig):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="black"
    )
    return fig

# ---------------------------
# SUPABASE CONFIG (🔥 FIXED)
# ---------------------------
URL = "https://ckslcleodlomdbttzeac.supabase.co/rest/v1/sss_schedule"

KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrc2xjbGVvZGxvbWRidHR6ZWFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMxNjY2NSwiZXhwIjoyMDkxODkyNjY1fQ.duxCrrLqpMZ2LMZ3S3-C_DyiqZ5Vjhr2td1d2FSkBTA"
   # 🔥 PUT FULL KEY

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}"
}

# ---------------------------
# LOAD DATA (🔥 ONLY CHANGE)
# ---------------------------
@st.cache_data
def load_data():
    params = {
        "select": "*",
        "limit": 100000
    }

    res = requests.get(URL, headers=headers, params=params)

    if res.status_code != 200:
        st.error(res.text)
        st.stop()

    df = pd.DataFrame(res.json())

    # clean
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    return df

df = load_data()

# ---------------------------
# DATE PARSE
# ---------------------------
def parse_date(x):
    x = str(x).strip()
    try:
        return pd.to_datetime(x, dayfirst=True)
    except:
        return pd.NaT

df["Inserted_At"] = df["Inserted_At"].apply(parse_date)
df["Inserted_Date"] = df["Inserted_At"]

# ---------------------------
# TITLE
# ---------------------------
st.markdown('<div class="title">SSS DATA ANALYTICS</div>', unsafe_allow_html=True)

# ---------------------------
# FILTERS
# ---------------------------
st.markdown("### Filters")

col1, col2, col3, col4 = st.columns(4)

operator = col1.multiselect("Operator", sorted(df["Operator_Code"].unique()))
service = col2.multiselect("Service", sorted(df["Service"].unique()))
from_port = col3.multiselect("From Port", sorted(df["From_Port"].unique()))
to_port = col4.multiselect("To Port", sorted(df["To_Port"].unique()))

filtered_df = df.copy()

if operator:
    filtered_df = filtered_df[filtered_df["Operator_Code"].isin(operator)]
if service:
    filtered_df = filtered_df[filtered_df["Service"].isin(service)]
if from_port:
    filtered_df = filtered_df[filtered_df["From_Port"].isin(from_port)]
if to_port:
    filtered_df = filtered_df[filtered_df["To_Port"].isin(to_port)]

filtered_df = filtered_df.dropna(subset=["Inserted_Date", "Operator_Code"])

# ---------------------------
# KPI
# ---------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Operators", filtered_df["Operator_Code"].nunique())
c2.metric("Ports", filtered_df["From_Port"].nunique())
c3.metric("Terminals", filtered_df["From_Port_Terminal"].nunique())
c4.metric("Vessels", filtered_df["Vessel_Name"].nunique())

# ---------------------------
# SUMMARY
# ---------------------------
summary_df = (
    filtered_df.groupby(["Inserted_Date", "Operator_Code"])
    .size()
    .reset_index(name="Count")
)

st.dataframe(summary_df, use_container_width=True)

# ---------------------------
# CHART
# ---------------------------
trend = filtered_df["Operator_Code"].value_counts().reset_index()
trend.columns = ["Operator", "Count"]

fig = px.bar(trend, x="Operator", y="Count", color="Operator")
st.plotly_chart(style_chart(fig), use_container_width=True)

# ---------------------------
# ROUTES
# ---------------------------
route_df = (
    filtered_df.groupby(["From_Port", "To_Port"])
    .size()
    .reset_index(name="Count")
)

route_df["Route"] = route_df["From_Port"] + " → " + route_df["To_Port"]

fig_route = px.bar(
    route_df.sort_values(by="Count", ascending=False).head(10),
    x="Count",
    y="Route",
    orientation="h"
)

st.plotly_chart(fig_route, use_container_width=True)

# ---------------------------
# MAP
# ---------------------------
if os.path.exists("country_lat_lon.csv"):
    country_df = pd.read_csv("country_lat_lon.csv")

    country_df["Country_Code"] = country_df["Country_Code"].str.upper()

    map_df = filtered_df.copy()

    map_df["From_Country"] = map_df["From_Port_Code"].str[:2]
    map_df["To_Country"] = map_df["To_Port_Code"].str[:2]

    route_df = (
        map_df.groupby(["From_Country", "To_Country"])
        .size()
        .reset_index(name="Count")
    )

    route_df = route_df.merge(
        country_df, left_on="From_Country", right_on="Country_Code"
    ).rename(columns={"Latitude": "from_lat", "Longitude": "from_lon"})

    route_df = route_df.merge(
        country_df, left_on="To_Country", right_on="Country_Code"
    ).rename(columns={"Latitude": "to_lat", "Longitude": "to_lon"})

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=route_df,
        get_source_position=["from_lon", "from_lat"],
        get_target_position=["to_lon", "to_lat"],
        get_width=1
    )

    st.pydeck_chart(pdk.Deck(layers=[arc_layer]))
else:
    st.warning("country_lat_lon.csv not found")
