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

def style_chart(fig):   # ✅ FIX 2 (missing function)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="black"
    )
    return fig

# ---------------------------
# GRADIENT CSS (🔥 PREMIUM)
# ---------------------------
st.markdown("""
<style>

/* Title */
.title {
    background: linear-gradient(90deg, #667eea, #764ba2, #43cea2);
    padding: 18px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: white;
    border-radius: 12px;
    margin-bottom: 20px;
}

/* Section */
.section {
    background: linear-gradient(90deg, #36d1dc, #5b86e5);
    padding: 10px;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    margin-top: 25px;
}

/* Cards */
.card {
    padding: 25px;
    border-radius: 14px;
    color: white;
    text-align: center;
    font-weight: bold;
}

/* Card colors */
.card1 { background: linear-gradient(135deg, #667eea, #764ba2); }
.card2 { background: linear-gradient(135deg, #43cea2, #185a9d); }
.card3 { background: linear-gradient(135deg, #36d1dc, #5b86e5); }
.card4 { background: linear-gradient(135deg, #ff758c, #ff7eb3); }

</style>
""", unsafe_allow_html=True)


# ---------------------------
# TITLE
# ---------------------------
st.markdown('<div class="title">SSS DATA ANALYTICS</div>', unsafe_allow_html=True)

# SUPABASE CONFIG
# ---------------------------
URL = "https://ckslcleodlomdbttzeac.supabase.co/rest/v1/sss_schedule"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrc2xjbGVvZGxvbWRidHR6ZWFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMxNjY2NSwiZXhwIjoyMDkxODkyNjY1fQ.duxCrrLqpMZ2LMZ3S3-C_DyiqZ5Vjhr2td1d2FSkBTA"   # 🔥 replace with your key

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}"
}

# ---------------------------
# LOAD DATA (🔥 FIXED - FULL DATA)
# ---------------------------
@st.cache_data
def load_data():
    all_data = []
    batch_size = 1000
    start = 0

    while True:
        headers_range = headers.copy()
        headers_range["Range"] = f"{start}-{start + batch_size - 1}"

        res = requests.get(URL, headers=headers_range)

        if res.status_code != 200:
            st.error(res.text)
            st.stop()

        data = res.json()

        if not data:
            break

        all_data.extend(data)

        if len(data) < batch_size:
            break

        start += batch_size

    df = pd.DataFrame(all_data)

    df.columns = df.columns.str.strip()
    df = df.fillna("")

    return df

df = load_data()

# ---------------------------
# DATE PARSE
# ---------------------------
def parse_date(x):
    try:
        return pd.to_datetime(x, dayfirst=True)
    except:
        return pd.NaT

df["Inserted_At"] = df["Inserted_At"].apply(parse_date)
df["Inserted_Date"] = df["Inserted_At"]


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
# KPI CARDS
# ---------------------------

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f'<div class="card card1">TOTAL OPERATORS<br><h1>{filtered_df["Operator_Code"].nunique()}</h1></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card card2">TOTAL PORTS<br><h1>{filtered_df["From_Port"].nunique()}</h1></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card card3">TOTAL TERMINALS<br><h1>{filtered_df["From_Port_Terminal"].nunique()}</h1></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="card card4">TOTAL VESSELS<br><h1>{filtered_df["Vessel_Name"].nunique()}</h1></div>', unsafe_allow_html=True)


# ---------------------------
# SUMMARY TABLE
# ---------------------------
st.markdown('<div class="section">Date vs Operator Summary</div>', unsafe_allow_html=True)

summary_df = (
    filtered_df.groupby(["Inserted_Date", "Operator_Code"])
    .size()
    .reset_index(name="Count")
)

summary_df["Inserted_Date"] = summary_df["Inserted_Date"].dt.strftime("%d-%m-%Y")

total = pd.DataFrame({
    "Inserted_Date": ["TOTAL"],
    "Operator_Code": [""],
    "Count": [summary_df["Count"].sum()]
})

final_df = pd.concat([summary_df, total])

st.dataframe(final_df, width='stretch')

# ---------------------------
# OPERATOR ANALYTICS
# ---------------------------
st.markdown("### Operator Analytics")

trend = filtered_df["Operator_Code"].value_counts().reset_index()
trend.columns = ["Operator", "Count"]

fig = px.bar(trend, x="Operator", y="Count", color="Operator", text="Count")
fig.update_traces(textposition="outside")
fig.update_layout(showlegend=False)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# TOP ROUTES
# ---------------------------
st.markdown("### Top Routes")

route_df = (
    filtered_df.groupby(["From_Port", "To_Port"])
    .size()
    .reset_index(name="Count")
)

route_df["Route"] = route_df["From_Port"] + " → " + route_df["To_Port"]
route_df = route_df.sort_values(by="Count", ascending=False).head(10)

fig_route = px.bar(
    route_df,
    x="Count",
    y="Route",
    orientation="h",
    color="Route"
)

st.plotly_chart(fig_route, use_container_width=True)

# ---------------------------
# SERVICE DISTRIBUTION
# ---------------------------
st.markdown("### Service Distribution")

service_df = filtered_df["Service"].value_counts().reset_index()
service_df.columns = ["Service", "Count"]

fig_service = px.bar(service_df.head(10), x="Count", y="Service", orientation="h")
st.plotly_chart(fig_service, use_container_width=True)

# ---------------------------
# MAP
# ---------------------------
# if os.path.exists("country_lat_lon.csv"):

#     country_df = pd.read_csv("country_lat_lon.csv")
#     country_df["Country_Code"] = country_df["Country_Code"].str.upper()

#     map_df = filtered_df.copy()
#     map_df["From_Country"] = map_df["From_Port_Code"].str[:2]
#     map_df["To_Country"] = map_df["To_Port_Code"].str[:2]

#     route_df = (
#         map_df.groupby(["From_Country", "To_Country"])
#         .size()
#         .reset_index(name="Count")
#     )

#     route_df = route_df.merge(
#         country_df, left_on="From_Country", right_on="Country_Code"
#     ).rename(columns={"Latitude": "from_lat", "Longitude": "from_lon"})

#     route_df = route_df.merge(
#         country_df, left_on="To_Country", right_on="Country_Code"
#     ).rename(columns={"Latitude": "to_lat", "Longitude": "to_lon"})

#     arc_layer = pdk.Layer(
#         "ArcLayer",
#         data=route_df,
#         get_source_position=["from_lon", "from_lat"],
#         get_target_position=["to_lon", "to_lat"],
#         get_width=1,
#     )

#     st.markdown("### Route Map")
#     st.pydeck_chart(pdk.Deck(layers=[arc_layer]))

# else:
#     st.warning("country_lat_lon.csv not found")
