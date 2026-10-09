import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import psycopg2

# Ensure UTF-8 handling in terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# =============================================================================
# 1. Page Configuration & Custom CSS
# =============================================================================
st.set_page_config(
    page_title="Egyptian MOI Crime Intelligence Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern executive dashboard look
st.markdown("""
<style>
    .metric-card {
        background: #1e222d;
        border: 1px solid #2d3343;
        border-radius: 8px;
        padding: 18px;
        text-align: center;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        margin-bottom: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.85rem;
        color: #58a6ff;
        font-weight: 700;
    }
    .badge-postgres {
        background-color: #238636;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-parquet {
        background-color: #d29922;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. Database Connection & Environment Helpers
# =============================================================================
def load_env_credentials():
    """Load database environment variables from .env if present."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


# Governorate & Crime Type lookup dictionaries for Parquet fallback mode
DIM_LOCATION_MAP = {
    0: ("غير محدد", "Unknown", "Unknown"),
    1: ("القاهرة", "Cairo", "Greater Cairo"),
    2: ("الجيزة", "Giza", "Greater Cairo"),
    3: ("القليوبية", "Qalyubia", "Greater Cairo"),
    4: ("الإسكندرية", "Alexandria", "Delta"),
    5: ("البحيرة", "Beheira", "Delta"),
    6: ("كفر الشيخ", "Kafr El Sheikh", "Delta"),
    7: ("الغربية", "Gharbia", "Delta"),
    8: ("المنوفية", "Monufia", "Delta"),
    9: ("الدقهلية", "Dakahlia", "Delta"),
    10: ("الشرقية", "Sharqia", "Delta"),
    11: ("دمياط", "Damietta", "Delta"),
    12: ("بورسعيد", "Port Said", "Canal"),
    13: ("الإسماعيلية", "Ismailia", "Canal"),
    14: ("السويس", "Suez", "Canal"),
    15: ("الفيوم", "Faiyum", "Upper Egypt"),
    16: ("بني سويف", "Beni Suef", "Upper Egypt"),
    17: ("المنيا", "Minya", "Upper Egypt"),
    18: ("أسيوط", "Asyut", "Upper Egypt"),
    19: ("سوهاج", "Sohag", "Upper Egypt"),
    20: ("قنا", "Qena", "Upper Egypt"),
    21: ("الأقصر", "Luxor", "Upper Egypt"),
    22: ("أسوان", "Aswan", "Upper Egypt"),
    23: ("البحر الأحمر", "Red Sea", "Frontier"),
    24: ("الوادي الجديد", "New Valley", "Frontier"),
    25: ("مطروح", "Matrouh", "Frontier"),
    26: ("شمال سيناء", "North Sinai", "Frontier"),
    27: ("جنوب سيناء", "South Sinai", "Frontier"),
}

# Centroid coordinates (lat, lon) for Egyptian Governorates
EGYPT_GOV_COORDS = {
    # Greater Cairo
    "القاهرة": (30.0444, 31.2357),
    "الجيزة": (30.0131, 31.2089),
    "القليوبية": (30.4660, 31.1856),
    # Alexandria & Delta
    "الإسكندرية": (31.2001, 29.9187),
    "البحيرة": (31.0364, 30.4699),
    "كفر الشيخ": (31.1107, 30.9388),
    "الغربية": (30.7865, 31.0004),
    "المنوفية": (30.5972, 30.9876),
    "الدقهلية": (31.0409, 31.3785),
    "الشرقية": (30.5877, 31.5020),
    "دمياط": (31.4175, 31.8144),
    # Canal Zone
    "بورسعيد": (31.2653, 32.3019),
    "الإسماعيلية": (30.5965, 32.2715),
    "السويس": (29.9668, 32.5498),
    # Upper Egypt
    "الفيوم": (29.3084, 30.8428),
    "بني سويف": (29.0661, 31.0994),
    "المنيا": (28.0871, 30.7618),
    "أسيوط": (27.1783, 31.1859),
    "سوهاج": (26.5590, 31.6957),
    "قنا": (26.1551, 32.7160),
    "الأقصر": (25.6872, 32.6396),
    "أسوان": (24.0889, 32.8998),
    # Frontier
    "البحر الأحمر": (27.2579, 33.8116),
    "الوادي الجديد": (25.4514, 30.5464),
    "مطروح": (31.3543, 27.2373),
    "شمال سيناء": (31.1316, 33.7984),
    "جنوب سيناء": (28.2431, 33.6231),
}

DIM_CRIME_MAP = {
    0: ("غير مصنف / أخرى", "Unclassified / Other", 1),
    1: ("بلطجة وفرض سيطرة", "Thuggery & Coercion", 4),
    2: ("تجارة المواد المخدرة", "Narcotics Trafficking", 4),
    3: ("حيازة أسلحة نارية وذخائر", "Illicit Firearms & Ammo", 4),
    4: ("سرقة بالإكراه وتشكيل عصابي", "Armed Robbery & Gangs", 5),
    5: ("سرقة مساكن ومتاجر", "Burglary & Larceny", 2),
    6: ("نصب واحتيال وتوظيف أموال", "Fraud & Ponzi Schemes", 3),
    7: ("جرائم إلكترونية وابتزاز", "Cybercrime & Extortion", 3),
    8: ("غسيل أموال وكسب غير مشروع", "Money Laundering & Illicit Gains", 4),
    9: ("شروع في قتل وقتل عمد", "Homicide & Attempted Murder", 5),
    10: ("تهريب وجرائم جمركية", "Smuggling & Customs Evasion", 3),
    11: ("مخالفات تموينية واحتكار", "Price Gouging & Supply Fraud", 1),
    12: ("تزوير محررات رسمية وعملات", "Counterfeiting & Forgery", 3),
}


@st.cache_data(ttl=600, show_spinner="Querying Gold Warehouse...")
def load_data():
    """
    Primary: Connects to local PostgreSQL Gold Warehouse.
    Fallback: Reads directly from Silver Parquet if DB is unreachable (e.g. cloud deployment).
    """
    load_env_credentials()
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "moi_crime_dw")
    db_user = os.environ.get("DB_USER", "postgres")
    db_pass = os.environ.get("DB_PASSWORD", "")

    # Try PostgreSQL first
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass,
            connect_timeout=3
        )
        query = """
            SELECT 
                f.crime_fact_id,
                f.news_id,
                d.calendar_date,
                d.year,
                d.month,
                d.month_name,
                d.day_name,
                d.is_weekend,
                l.governorate_ar,
                l.governorate_en,
                l.region,
                c.category_ar,
                c.category_en,
                c.severity_level,
                f.title,
                f.full_details,
                f.source_url,
                f.incident_count,
                f.suspects_count,
                f.weapons_count,
                f.is_campaign,
                f.published_timestamp
            FROM fact_crime f
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_location l ON f.location_id = l.location_id
            JOIN dim_crime_type c ON f.crime_type_id = c.crime_type_id
            ORDER BY f.published_timestamp DESC;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        df["calendar_date"] = pd.to_datetime(df["calendar_date"])
        return df, "PostgreSQL (Gold Warehouse)"
    except Exception:
        # Fallback to local Silver Parquet
        parquet_path = Path(__file__).parent / "silver_crime_news.parquet"
        if not parquet_path.exists():
            raise FileNotFoundError("Neither PostgreSQL nor silver_crime_news.parquet is accessible.")
        
        df = pd.read_parquet(parquet_path)
        
        # Enrich dimensions using in-memory taxonomy
        df["governorate_ar"] = df["location_id"].apply(lambda x: DIM_LOCATION_MAP.get(x, ("غير محدد", "", ""))[0])
        df["governorate_en"] = df["location_id"].apply(lambda x: DIM_LOCATION_MAP.get(x, ("", "Unknown", ""))[1])
        df["region"] = df["location_id"].apply(lambda x: DIM_LOCATION_MAP.get(x, ("", "", "Unknown"))[2])
        
        df["category_ar"] = df["crime_type_id"].apply(lambda x: DIM_CRIME_MAP.get(x, ("غير مصنف", "", 1))[0])
        df["category_en"] = df["crime_type_id"].apply(lambda x: DIM_CRIME_MAP.get(x, ("", "Unclassified", 1))[1])
        df["severity_level"] = df["crime_type_id"].apply(lambda x: DIM_CRIME_MAP.get(x, ("", "", 1))[2])
        
        df["calendar_date"] = pd.to_datetime(df["published_timestamp"]).dt.date
        df["calendar_date"] = pd.to_datetime(df["calendar_date"])
        df["year"] = df["calendar_date"].dt.year
        df["month"] = df["calendar_date"].dt.month
        df["month_name"] = df["calendar_date"].dt.strftime("%B")
        df["day_name"] = df["calendar_date"].dt.strftime("%A")
        df["is_weekend"] = df["calendar_date"].dt.dayofweek.isin([4, 5])
        
        return df, "Local Parquet (Silver Warehouse Backup)"


# Load enriched warehouse data
try:
    df_raw, data_source = load_data()
except Exception as e:
    st.error(f"❌ Failed to load warehouse data: {e}")
    st.stop()


# =============================================================================
# 3. Sidebar Filters
# =============================================================================
with st.sidebar:
    st.markdown("### 🏛️ Pipeline Control Center")
    if "PostgreSQL" in data_source:
        st.markdown(f'<span class="badge-postgres">🟢 {data_source}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-parquet">🟡 {data_source}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🔍 Filter Criteria")

    # Date Range Filter
    min_date = df_raw["calendar_date"].min().date()
    max_date = df_raw["calendar_date"].max().date()
    
    selected_date_range = st.date_input(
        "Incident Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Governorate Multi-select
    all_governorates = sorted([g for g in df_raw["governorate_ar"].unique() if g != "غير محدد"])
    selected_govs = st.multiselect(
        "Egyptian Governorates:",
        options=all_governorates,
        default=[]
    )

    # Crime Category Multi-select
    all_crimes = sorted([c for c in df_raw["category_ar"].unique() if "غير مصنف" not in c])
    selected_crimes = st.multiselect(
        "Crime Categories:",
        options=all_crimes,
        default=[]
    )

    # Severity Slider
    min_severity, max_severity = st.slider(
        "Severity Level (1: Minor to 5: High Risk):",
        min_value=1,
        max_value=5,
        value=(1, 5)
    )

    # Security Campaigns toggle
    campaigns_only = st.checkbox("🚨 Coordinated Campaigns Only", value=False)

    # Text Keyword Search
    search_keyword = st.text_input("🔎 Search Keywords (Arabic):", "")

    st.markdown("---")
    st.caption("DEPI Microsoft Data Engineering · Capstone")
    st.caption(f"Warehouse Records: **{len(df_raw):,}** articles")


# Apply Filters
df_filtered = df_raw.copy()

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_d, end_d = selected_date_range
    df_filtered = df_filtered[
        (df_filtered["calendar_date"].dt.date >= start_d) &
        (df_filtered["calendar_date"].dt.date <= end_d)
    ]

if selected_govs:
    df_filtered = df_filtered[df_filtered["governorate_ar"].isin(selected_govs)]

if selected_crimes:
    df_filtered = df_filtered[df_filtered["category_ar"].isin(selected_crimes)]

df_filtered = df_filtered[
    (df_filtered["severity_level"] >= min_severity) &
    (df_filtered["severity_level"] <= max_severity)
]

if campaigns_only:
    df_filtered = df_filtered[df_filtered["is_campaign"] == True]

if search_keyword.strip():
    kw = search_keyword.strip().lower()
    df_filtered = df_filtered[
        df_filtered["title"].str.lower().str.contains(kw, na=False) |
        df_filtered["full_details"].str.lower().str.contains(kw, na=False)
    ]


# =============================================================================
# 4. Header & Executive KPI Cards
# =============================================================================
st.title("⚖️ Egyptian MOI Crime Intelligence Platform")
st.markdown(
    "**End-to-End Medallion Architecture Data Pipeline** · "
    "*Ingested from Egyptian Ministry of Interior official releases (2019 – 2026)*"
)

# KPI Row
c1, c2, c3, c4 = st.columns(4)

total_incidents = len(df_filtered)
total_suspects = int(df_filtered["suspects_count"].sum())
total_weapons = int(df_filtered["weapons_count"].sum())
total_campaigns = int(df_filtered["is_campaign"].sum())

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Incidents</div>
        <div class="metric-value">{total_incidents:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Suspects Apprehended</div>
        <div class="metric-value">{total_suspects:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Weapons / Firearms Seized</div>
        <div class="metric-value">{total_weapons:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Security Campaigns</div>
        <div class="metric-value">{total_campaigns:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# 5. Tabbed Analytics & Serving
# =============================================================================
tab_geo, tab_trends, tab_crimes, tab_data, tab_nlp = st.tabs([
    "🗺️ Geographic Distribution",
    "📈 Temporal Trends",
    "⚖️ Crime Categories & Severity",
    "📋 Data Explorer",
    "🤖 Live Arabic Crime Classifier"
])


# -----------------------------------------------------------------------------
# TAB 1: GEOGRAPHIC DISTRIBUTION & EGYPT HEATMAP
# -----------------------------------------------------------------------------
with tab_geo:
    st.subheader("🗺️ Geographic Crime Hotspots & Egypt Heatmap")

    # Map controls header
    map_col1, map_col2 = st.columns([3, 1])
    with map_col1:
        st.markdown("*Interactive spatial view across all 27 Egyptian governorates*")
    with map_col2:
        map_mode = st.radio(
            "Map Visualization:",
            options=["🔥 Density Heatmap", "📍 Hotspot Bubbles"],
            horizontal=True
        )

    # Aggregate by governorate with coordinates
    geo_df = (
        df_filtered[df_filtered["governorate_ar"].isin(EGYPT_GOV_COORDS.keys())]
        .groupby(["governorate_ar", "governorate_en", "region"])
        .agg(
            incidents=("incident_count", "sum"),
            suspects=("suspects_count", "sum"),
            weapons=("weapons_count", "sum")
        )
        .reset_index()
    )

    if not geo_df.empty:
        geo_df["lat"] = geo_df["governorate_ar"].map(lambda g: EGYPT_GOV_COORDS[g][0])
        geo_df["lon"] = geo_df["governorate_ar"].map(lambda g: EGYPT_GOV_COORDS[g][1])

        if map_mode == "🔥 Density Heatmap":
            fig_map = px.density_map(
                geo_df,
                lat="lat",
                lon="lon",
                z="incidents",
                radius=32,
                center=dict(lat=26.8, lon=30.8),
                zoom=5,
                map_style="carto-darkmatter",
                color_continuous_scale="Reds",
                title="Egypt Crime Density Heatmap"
            )
        else:
            fig_map = px.scatter_map(
                geo_df,
                lat="lat",
                lon="lon",
                size="incidents",
                color="incidents",
                hover_name="governorate_ar",
                hover_data={
                    "governorate_en": True,
                    "incidents": True,
                    "suspects": True,
                    "weapons": True,
                    "lat": False,
                    "lon": False
                },
                center=dict(lat=26.8, lon=30.8),
                zoom=5,
                map_style="carto-darkmatter",
                color_continuous_scale="Reds",
                size_max=35,
                title="Egyptian Governorates Crime Hotspots"
            )

        fig_map.update_layout(
            template="plotly_dark",
            margin=dict(l=0, r=0, t=35, b=0),
            height=460
        )
        st.plotly_chart(fig_map, width="stretch")
    else:
        st.info("No geographic data matching current filters.")

    st.markdown("---")
    st.subheader("Governorate & Regional Breakdowns")
    
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Top 15 Governorates (excluding Unknown)
        gov_counts = (
            df_filtered[df_filtered["governorate_ar"] != "غير محدد"]["governorate_ar"]
            .value_counts()
            .reset_index()
        )
        gov_counts.columns = ["governorate_ar", "incidents"]
        
        if not gov_counts.empty:
            fig_gov = px.bar(
                gov_counts.head(15),
                x="incidents",
                y="governorate_ar",
                orientation="h",
                title="Top 15 Egyptian Governorates by Incident Volume",
                labels={"incidents": "Reported Incidents", "governorate_ar": "Governorate"},
                color="incidents",
                color_continuous_scale="Reds"
            )
            fig_gov.update_layout(yaxis={"categoryorder": "total ascending"}, template="plotly_dark")
            st.plotly_chart(fig_gov, width="stretch")
        else:
            st.info("No governorate data matching current filters.")

    with col_right:
        # Regional Breakdown
        region_counts = (
            df_filtered[df_filtered["region"] != "Unknown"]["region"]
            .value_counts()
            .reset_index()
        )
        region_counts.columns = ["region", "incidents"]
        
        if not region_counts.empty:
            fig_region = px.pie(
                region_counts,
                names="region",
                values="incidents",
                hole=0.45,
                title="Distribution by Administrative Region",
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_region, width="stretch")
        else:
            st.info("No regional data matching current filters.")


# -----------------------------------------------------------------------------
# TAB 2: TEMPORAL TRENDS
# -----------------------------------------------------------------------------
with tab_trends:
    st.subheader("Historical Timeline & Seasonality Analysis (2019 – 2026)")
    
    col_t1, col_t2 = st.columns([3, 2])
    
    with col_t1:
        # Monthly Timeline
        df_monthly = df_filtered.copy()
        df_monthly["year_month"] = df_monthly["calendar_date"].dt.to_period("M").dt.to_timestamp()
        monthly_counts = df_monthly.groupby("year_month").size().reset_index(name="incident_count")
        
        if not monthly_counts.empty:
            fig_trend = px.line(
                monthly_counts,
                x="year_month",
                y="incident_count",
                title="Monthly Crime Release Volume",
                labels={"year_month": "Month", "incident_count": "Incidents"},
                markers=True,
                template="plotly_dark"
            )
            fig_trend.update_traces(line_color="#58a6ff")
            st.plotly_chart(fig_trend, width="stretch")
        else:
            st.info("No timeline data matching current filters.")

    with col_t2:
        # Day of Week Distribution
        days_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_counts = df_filtered["day_name"].value_counts().reindex(days_order).reset_index()
        day_counts.columns = ["day_name", "incidents"]
        
        fig_day = px.bar(
            day_counts,
            x="day_name",
            y="incidents",
            title="Incidents by Day of the Week",
            labels={"day_name": "Day", "incidents": "Incidents"},
            template="plotly_dark",
            color="incidents",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_day, width="stretch")


# -----------------------------------------------------------------------------
# TAB 3: CRIME CATEGORIES & SEVERITY
# -----------------------------------------------------------------------------
with tab_crimes:
    st.subheader("Crime Taxonomy & Risk Severity Analysis")
    
    col_c1, col_c2 = st.columns([3, 2])
    
    with col_c1:
        # Crime Categories
        crime_counts = (
            df_filtered[~df_filtered["category_ar"].str.contains("غير مصنف", na=False)]["category_ar"]
            .value_counts()
            .reset_index()
        )
        crime_counts.columns = ["category_ar", "incidents"]
        
        if not crime_counts.empty:
            fig_crimes = px.bar(
                crime_counts,
                x="incidents",
                y="category_ar",
                orientation="h",
                title="Crime Incidents by Standardized Taxonomy",
                labels={"incidents": "Count", "category_ar": "Crime Category"},
                template="plotly_dark",
                color="incidents",
                color_continuous_scale="Purples"
            )
            fig_crimes.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_crimes, width="stretch")
        else:
            st.info("No category data matching current filters.")

    with col_c2:
        # Severity Level breakdown
        sev_counts = df_filtered["severity_level"].value_counts().sort_index().reset_index()
        sev_counts.columns = ["severity_level", "count"]
        sev_labels = {
            1: "1 - Public Order",
            2: "2 - Property/Theft",
            3: "3 - Fraud & Cyber",
            4: "4 - Narcotics & Arms",
            5: "5 - Homicide & Gangs"
        }
        sev_counts["label"] = sev_counts["severity_level"].map(sev_labels)
        
        fig_sev = px.pie(
            sev_counts,
            names="label",
            values="count",
            hole=0.45,
            title="Distribution by Severity Risk Level",
            template="plotly_dark",
            color_discrete_sequence=px.colors.sequential.Inferno
        )
        st.plotly_chart(fig_sev, width="stretch")


# -----------------------------------------------------------------------------
# TAB 4: DATA EXPLORER & WAREHOUSE EXPORT
# -----------------------------------------------------------------------------
with tab_data:
    st.subheader("Warehouse Table Explorer")
    st.markdown(f"Displaying **{len(df_filtered):,}** records matching current filters.")
    
    export_cols = [
        "calendar_date",
        "governorate_ar",
        "category_ar",
        "severity_level",
        "title",
        "suspects_count",
        "weapons_count",
        "is_campaign",
        "source_url"
    ]
    
    display_df = df_filtered[export_cols].copy()
    display_df.columns = [
        "Date", "Governorate", "Category", "Severity", "Title",
        "Suspects", "Weapons", "Campaign", "Source URL"
    ]
    
    st.dataframe(
        display_df,
        column_config={
            "Source URL": st.column_config.LinkColumn("Source URL", display_text="Open News")
        },
        width="stretch",
        height=450
    )
    
    # CSV Download Button
    csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Export Filtered Warehouse Data (CSV)",
        data=csv_bytes,
        file_name=f"moi_crime_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


# -----------------------------------------------------------------------------
# TAB 5: LIVE ARABIC CRIME CLASSIFIER (PIPELINE DEMO)
# -----------------------------------------------------------------------------
with tab_nlp:
    st.subheader("🤖 Live Arabic NLP Crime Analyzer")
    st.markdown(
        "Test our data engineering extraction & normalization logic in real-time. "
        "Paste any Arabic police press release or crime report below:"
    )
    
    sample_text = (
        "تمكنت الأجهزة الأمنية بمديرية أمن القاهرة من ضبط 3 عاطلين بحوزتهم "
        "كمية من مخدر الحشيش وسلاح ناري فرد خرطوش وعدد من الطلقات بدائرة قسم شرطة المعادي."
    )
    
    user_input = st.text_area(
        "Arabic Crime Report / Dispatch Text:",
        value=sample_text,
        height=120
    )
    
    if st.button("🚀 Run Extraction & Classification Pipeline", type="primary"):
        # Import extraction engine from transform_silver.py
        try:
            from transform_silver import (
                extract_location_id,
                extract_crime_type_id,
                extract_metrics,
                GOVERNORATES,
                CRIME_TAXONOMY
            )
            
            loc_id = extract_location_id(user_input, user_input)
            crime_id = extract_crime_type_id(user_input, user_input)
            suspects, weapons, is_camp = extract_metrics(user_input, user_input)
            
            gov_info = DIM_LOCATION_MAP.get(loc_id, ("غير محدد", "Unknown", "Unknown"))
            crime_info = DIM_CRIME_MAP.get(crime_id, ("غير مصنف", "Unclassified", 1))
            
            st.success("✅ Text Processed Through Silver Normalization Engine!")
            
            res_c1, res_c2, res_c3, res_c4, res_c5 = st.columns(5)
            
            with res_c1:
                st.metric("Governorate", f"{gov_info[0]} ({gov_info[1]})")
            with res_c2:
                st.metric("Crime Category", crime_info[0])
            with res_c3:
                st.metric("Severity Level", f"Level {crime_info[2]} / 5")
            with res_c4:
                st.metric("Suspects Count", suspects)
            with res_c5:
                st.metric("Weapons Seized", weapons)
                
            if is_camp:
                st.warning("🚨 Coordinated Security Campaign Detected!")
            else:
                st.info("ℹ️ Standard Incident / Individual Arrest")
                
        except Exception as err:
            st.error(f"Error executing extraction engine: {err}")
