import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import os
import pydeck as pdk

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="SSS Dashboard", layout="wide")

# ---------------------------
# ERROR HANDLER
# ---------------------------
try:

    # ---------------------------
    # STYLE FUNCTION
    # ---------------------------
    def style_chart(fig):
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_color="black"
        )
        return fig

    # ---------------------------
    # TITLE
    # ---------------------------
    st.markdown("## SSS DATA ANALYTICS")

    # ---------------------------
    # LOAD DATA (SAFE)
    # ---------------------------
    @st.cache_data
    def load_data():
        files = os.listdir()
        zip_files = [f for f in files if f.endswith(".zip")]

        if not zip_files:
            st.error("❌ No ZIP file found")
            st.write("Available files:", files)
            st.stop()

        with zipfile.ZipFile(zip_files[0]) as z:
            csv_files = [f for f in z.namelist() if f.endswith(".csv")]

            if not csv_files:
                st.error("❌ No CSV inside ZIP")
                st.stop()

            with z.open(csv_files[0]) as f:
                df = pd.read_csv(f, encoding="cp1252", low_memory=False, dtype=str)

        return df

    df = load_data()

    # ---------------------------
    # DEBUG (IMPORTANT)
    # ---------------------------
    st.write("Columns:", df.columns.tolist())

    # ---------------------------
    # DATE FIX (SAFE)
    # ---------------------------
    if "Inserted_At" in df.columns:
        df["Inserted_At"] = pd.to_datetime(df["Inserted_At"], errors="coerce")
    else:
        st.error("❌ 'Inserted_At' column missing")
        st.stop()

    df["Inserted_Date"] = df["Inserted_At"]

    # ---------------------------
    # REQUIRED COLUMN CHECK
    # ---------------------------
    required_cols = [
        "Operator_Code", "Service",
        "From_Port", "To_Port",
        "From_Port_Terminal", "Vessel_Name"
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        st.error(f"❌ Missing columns: {missing_cols}")
        st.stop()

    # ---------------------------
    # FILTERS
    # ---------------------------
    st.markdown("### Filters")

    col1, col2, col3, col4 = st.columns(4)

    operator = col1.multiselect("Operator", sorted(df["Operator_Code"].dropna().unique()))
    service = col2.multiselect("Service", sorted(df["Service"].dropna().unique()))
    from_port = col3.multiselect("From Port", sorted(df["From_Port"].dropna().unique()))
    to_port = col4.multiselect("To Port", sorted(df["To_Port"].dropna().unique()))

    # ---------------------------
    # FILTER LOGIC
    # ---------------------------
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
    st.subheader("Date vs Operator Summary")

    summary_df = (
        filtered_df.groupby(["Inserted_Date", "Operator_Code"])
        .size()
        .reset_index(name="Count")
    )

    summary_df["Inserted_Date"] = summary_df["Inserted_Date"].dt.strftime("%d-%m-%Y")

    st.dataframe(summary_df, use_container_width=True)

    # ---------------------------
    # OPERATOR CHART
    # ---------------------------
    trend = filtered_df["Operator_Code"].value_counts().reset_index()
    trend.columns = ["Operator", "Count"]

    fig = px.bar(trend, x="Operator", y="Count", text="Count", color="Operator")
    fig.update_layout(showlegend=False)

    st.plotly_chart(style_chart(fig), use_container_width=True)

    # ---------------------------
    # ROUTES
    # ---------------------------
    st.subheader("Top Routes")

    route_df = (
        filtered_df.groupby(["From_Port", "To_Port"])
        .size()
        .reset_index(name="Count")
    )

    route_df["Route"] = route_df["From_Port"] + " → " + route_df["To_Port"]
    route_df = route_df.sort_values(by="Count", ascending=False).head(10)

    fig_route = px.bar(route_df, x="Count", y="Route", orientation="h")
    st.plotly_chart(fig_route, use_container_width=True)

    # ---------------------------
    # MAP FILE CHECK
    # ---------------------------
    if not os.path.exists("country_lat_lon.csv"):
        st.warning("⚠️ country_lat_lon.csv missing → map disabled")
    else:
        st.subheader("Route Map")

        country_df = pd.read_csv("country_lat_lon.csv")

        country_df.columns = country_df.columns.str.strip()

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
            country_df, left_on="From_Country", right_on="Country_Code", how="left"
        ).rename(columns={"Latitude": "from_lat", "Longitude": "from_lon"})

        route_df = route_df.merge(
            country_df, left_on="To_Country", right_on="Country_Code", how="left"
        ).rename(columns={"Latitude": "to_lat", "Longitude": "to_lon"})

        route_df = route_df.dropna()

        arc_layer = pdk.Layer(
            "ArcLayer",
            data=route_df,
            get_source_position=["from_lon", "from_lat"],
            get_target_position=["to_lon", "to_lat"],
            get_width=2,
        )

        st.pydeck_chart(pdk.Deck(layers=[arc_layer]))

# ---------------------------
# GLOBAL ERROR
# ---------------------------
except Exception as e:
    import traceback
    st.error(f"🔥 App crashed: {e}")
    st.text(traceback.format_exc())
