import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
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

# ---------------------------
# LOAD DATA
@st.cache_data
def load_data():
    zip_files = [f for f in os.listdir() if f.endswith(".zip")]

    if not zip_files:
        st.error("❌ No ZIP file found")
        st.stop()

    with zipfile.ZipFile(zip_files[0]) as z:
        csv_files = [f for f in z.namelist() if f.endswith(".csv")]

        if not csv_files:
            st.error("❌ No CSV inside ZIP")
            st.stop()

        with z.open(csv_files[0]) as f:
            df = pd.read_csv(
                f,
                encoding="cp1252",
                low_memory=False,
                dtype=str   # ✅ FIX 3 (prevent crash)
            )

    return df

df = load_data()

# ---------------------------
# DATE CLEAN FUNCTION (MOVE HERE)
# ---------------------------
def parse_date(x):
    x = str(x).strip()

    formats = [
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y"
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(x, format=fmt)
        except:
            continue

    return pd.NaT
# ---------------------------
# APPLY DATE PARSING (MISSING STEP)
# ---------------------------
df["Inserted_At"] = df["Inserted_At"].apply(parse_date)

# create Inserted_Date column
df["Inserted_Date"] = df["Inserted_At"]

        
# ---------------------------
# FILTERS
# ---------------------------
st.markdown("### Filters")

col1, col2, col3, col4 = st.columns(4)

operator = col1.multiselect(
    "Operator",
    sorted(df["Operator_Code"].dropna().astype(str).unique())
)

service = col2.multiselect(
    "Service",
    sorted(df["Service"].dropna().astype(str).unique())
)

from_port = col3.multiselect(
    "From Port",
    sorted(df["From_Port"].dropna().astype(str).unique())
)

to_port = col4.multiselect(
    "To Port",
    sorted(df["To_Port"].dropna().astype(str).unique())
)


# ---------------------------
# FILTER LOGIC (CORRECT)
# ---------------------------

filtered_df = df.copy()   # ✅ FIRST create

if operator:
    filtered_df = filtered_df[filtered_df["Operator_Code"].isin(operator)]
if service:
    filtered_df = filtered_df[filtered_df["Service"].isin(service)]
if from_port:
    filtered_df = filtered_df[filtered_df["From_Port"].isin(from_port)]
if to_port:
    filtered_df = filtered_df[filtered_df["To_Port"].isin(to_port)]

# ✅ THEN CLEAN
filtered_df = filtered_df.dropna(subset=["Inserted_Date", "Operator_Code"])

# ---------------------------
# KPI CARDS
# ---------------------------
#st.markdown('<div class="section">OVERALL SUMMARY</div>', unsafe_allow_html=True)

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
# CHART (NO GRID)
# ---------------------------
# st.markdown('<div class="section">DATE WISE OPERATOR DISTRIBUTION</div>', unsafe_allow_html=True)

# operator_trend = (
#     filtered_df.groupby(["Inserted_Date", "Operator_Code"])
#     .size()
#     .reset_index(name="Count")
# )

# fig = px.bar(
#     operator_trend,
#     x="Inserted_Date",
#     y="Count",
#     color="Operator_Code",
#     barmode="stack",
#     color_discrete_sequence=px.colors.qualitative.Bold
# )

# # REMOVE GRID 🔥
# fig.update_layout(
#     xaxis=dict(showgrid=False),
#     yaxis=dict(showgrid=False),
#     plot_bgcolor="white"
# )

# st.plotly_chart(fig, width='stretch')

# ---------------------------
# OPERATOR ANALYTICS (NEW)
# ---------------------------
st.markdown('<div class="section">Operator Analytics(15-04-2026)</div>', unsafe_allow_html=True)

# Prepare Data
trend = filtered_df["Operator_Code"].value_counts().reset_index()
trend.columns = ["Operator", "Count"]

# ---------------------------
# VIEW MODE TOGGLE
# ---------------------------
# view_mode = st.radio(
#     "Select View",
#     ["Top Operators (Bar)", "Treemap View"]
# )

# ---------------------------
# TOP OPERATORS (BAR CHART)
# ---------------------------
# if view_mode == "Top Operators (Bar)":

#     top_n = st.slider("Select Top Operators", 5, 30, 15)

#     top_df = trend.head(top_n)

#     others_count = trend["Count"][top_n:].sum()

#     if others_count > 0:
#         others_df = pd.DataFrame({
#             "Operator": ["OTHERS"],
#             "Count": [others_count]
#         })
#         final_trend = pd.concat([top_df, others_df])
#     else:
#         final_trend = top_df

fig = px.bar(
        trend,   # 🔥 THIS WAS MISSING
        x="Operator",
        y="Count",
        text="Count",
        color="Operator"
    )

fig.update_traces(textposition="outside")
fig.update_layout(showlegend=False)

st.plotly_chart(style_chart(fig), width='stretch')

# ---------------------------
# TREEMAP VIEW
# ---------------------------
# ---------------------------
# IMPROVED TREEMAP
# ---------------------------
# st.markdown('<div class="section">Operator Distribution (Clean Treemap)</div>', unsafe_allow_html=True)

# # Prepare Data
# trend = filtered_df["Operator_Code"].value_counts().reset_index()
# trend.columns = ["Operator", "Count"]

# # Top N selection
# top_n = st.slider("Treemap Top Operators", 5, 30, 15)

# top_df = trend.head(top_n)

# others_count = trend["Count"][top_n:].sum()

# if others_count > 0:
#     others_df = pd.DataFrame({
#         "Operator": ["OTHERS"],
#         "Count": [others_count]
#     })
#     treemap_df = pd.concat([top_df, others_df])
# else:
#     treemap_df = top_df

# Treemap
treemap_df = trend.copy()   # simple fix (or use your Top N logic)
fig_tree = px.treemap(
    treemap_df,
    path=["Operator"],
    values="Count",
    color="Count",
    color_continuous_scale="Blues"
)

# Improve layout
fig_tree.update_traces(
    textinfo="label+value",
    textfont_size=14
)

fig_tree.update_layout(
    margin=dict(t=30, l=10, r=10, b=10)
)

st.plotly_chart(style_chart(fig_tree), width='stretch')
# ---------------------------
# TOP ROUTES (PROPER COLORS)
# ---------------------------
st.markdown('<div class="section">TOP ROUTES</div>', unsafe_allow_html=True)

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
    color="Route",  # 🔥 each route gets unique color
    color_discrete_sequence=px.colors.qualitative.Set2  # clean palette
)

fig_route.update_layout(
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    plot_bgcolor="white",
    showlegend=False  # cleaner UI
)

st.plotly_chart(fig_route, width='stretch')
# ---------------------------
# SERVICE DISTRIBUTION
# ---------------------------
st.markdown('<div class="section">SERVICE DISTRIBUTION (TOP 10)</div>', unsafe_allow_html=True)

service_df = filtered_df["Service"].value_counts().reset_index()
service_df.columns = ["Service", "Count"]

# Top 10 + Others
top10 = service_df.head(10)
others = service_df["Count"][10:].sum()

if others > 0:
    top10.loc[len(top10)] = ["Others", others]

fig_service = px.bar(
    top10,
    x="Count",
    y="Service",
    orientation="h",
    color="Count",
    color_continuous_scale="Tealgrn"   # 🔥 clean gradient
)

fig_service.update_layout(
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    plot_bgcolor="white"
)

st.plotly_chart(fig_service, width='stretch')

# ---------------------------
# COMPARISON
# ---------------------------
st.markdown('<div class="section">Operator Comparison</div>', unsafe_allow_html=True)

op_list = filtered_df["Operator_Code"].unique()

op1 = st.selectbox("Operator 1", op_list)
op2 = st.selectbox("Operator 2", op_list)

st.write(f"{op1}: {len(filtered_df[filtered_df['Operator_Code']==op1])} records")
st.write(f"{op2}: {len(filtered_df[filtered_df['Operator_Code'] == op2])} records")

import pydeck as pdk
import pandas as pd
import streamlit as st

# =========================================================
# LOAD COUNTRY DATA
# =========================================================
import os

if os.path.exists("country_lat_lon.csv"):
    country_df = pd.read_csv("country_lat_lon.csv")
else:
    st.warning("⚠️ country_lat_lon.csv not found")
    st.stop()

country_df.columns = country_df.columns.str.strip()

# auto-handle column names
if "country_code" in country_df.columns:
    country_df = country_df.rename(columns={"country_code": "Country_Code"})
elif "Country" in country_df.columns:
    country_df = country_df.rename(columns={"Country": "Country_Code"})

if "latitude" in country_df.columns:
    country_df = country_df.rename(columns={"latitude": "Latitude"})

if "longitude" in country_df.columns:
    country_df = country_df.rename(columns={"longitude": "Longitude"})
required_cols = ["Country_Code", "Latitude", "Longitude"]

missing = [col for col in required_cols if col not in country_df.columns]

if missing:
    st.error(f"Missing columns in country file: {missing}")
    st.stop()

country_df["Country_Code"] = country_df["Country_Code"].astype(str).str.strip().str.upper()

# =========================================================
# PREPARE DATA
# =========================================================
map_df = filtered_df.copy()

# Clean column names
map_df.columns = map_df.columns.str.strip().str.replace(r"\s+", "_", regex=True)

# Clean port codes
map_df["From_Port_Code"] = map_df["From_Port_Code"].astype(str).str.strip().str.upper()
map_df["To_Port_Code"] = map_df["To_Port_Code"].astype(str).str.strip().str.upper()

# Extract country
map_df["From_Country"] = map_df["From_Port_Code"].str[:2]
map_df["To_Country"] = map_df["To_Port_Code"].str[:2]

# =========================================================
# GROUP ROUTES
# =========================================================
route_df = (
    map_df.groupby(["From_Country", "To_Country"])
    .size()
    .reset_index(name="Count")
)

# =========================================================
# USER CONTROL (🔥 KEY FEATURE)
# =========================================================
st.markdown("### Route Selection")

mode = st.radio(
    "Select View",
    ["Top Routes", "Select Specific Routes"]
)

# ---------------------------
# OPTION 1: TOP ROUTES
# ---------------------------
if mode == "Top Routes":
    top_n = st.slider("Select Top Routes", 5, 50, 20)
    route_df = route_df.sort_values(by="Count", ascending=False).head(top_n)

# ---------------------------
# OPTION 2: SELECT ROUTES
# ---------------------------
else:
    route_df["Route"] = route_df["From_Country"] + " → " + route_df["To_Country"]

    selected_routes = st.multiselect(
        "Select Routes",
        route_df["Route"].unique()
    )

    if selected_routes:
        route_df = route_df[route_df["Route"].isin(selected_routes)]

# =========================================================
# MERGE LAT/LON
# =========================================================
route_df = route_df.merge(
    country_df,
    left_on="From_Country",
    right_on="Country_Code",
    how="left"
).rename(columns={"Latitude": "from_lat", "Longitude": "from_lon"})

route_df = route_df.merge(
    country_df,
    left_on="To_Country",
    right_on="Country_Code",
    how="left",
    suffixes=("", "_to")
).rename(columns={"Latitude": "to_lat", "Longitude": "to_lon"})

# =========================================================
# REMOVE INVALID DATA
# =========================================================
route_df = route_df[
    route_df["from_lat"].notna() &
    route_df["from_lon"].notna() &
    route_df["to_lat"].notna() &
    route_df["to_lon"].notna()
]

# Safety check
if route_df.empty:
    st.warning("⚠️ No routes available for selected filters")
    st.stop()

# =========================================================
# ARC LAYER
# =========================================================
arc_layer = pdk.Layer(
    "ArcLayer",
    data=route_df,
    get_source_position=["from_lon", "from_lat"],
    get_target_position=["to_lon", "to_lat"],
    get_width=1,
    width_scale=1,
    great_circle=False,
    get_source_color=[0, 150, 255],
    get_target_color=[255, 100, 150],
)

# =========================================================
# VIEW SETTINGS
# =========================================================
view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1,
    pitch=30,
)

# =========================================================
# TOOLTIP
# =========================================================
tooltip = {
    "html": "<b>Route:</b> {From_Country} → {To_Country}<br><b>Count:</b> {Count}",
    "style": {"color": "white"}
}

# =========================================================
# DISPLAY MAP
# =========================================================
st.markdown("### Top Routes Map")

st.pydeck_chart(pdk.Deck(
    layers=[arc_layer],
    initial_view_state=view_state,
    tooltip=tooltip
))
