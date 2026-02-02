import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.opensky_client import OpenSkyClient
from src.etl.data_pipeline import FlightDataPipeline
from config.config import Config

# Page config
st.set_page_config(
    page_title="OpenSky Flight Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
@st.cache_resource
def init_client():
    config = Config()
    return OpenSkyClient(config.OPENSKY_CLIENT_ID, config.OPENSKY_CLIENT_SECRET)

@st.cache_resource
def init_pipeline():
    client = init_client()
    return FlightDataPipeline(client)

pipeline = init_pipeline()

# Sidebar
with st.sidebar:
    st.title("✈️ Flight Analytics")
    
    region = st.selectbox(
        "Region",
        options=['north_america', 'europe', 'asia'],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    aircraft_filter = st.selectbox(
        "Aircraft Filter",
        options=['all', 'light', 'small', 'large', 'heavy'],
        format_func=lambda x: x.title()
    )
    
    country_filter = st.selectbox("Country Focus", ['all'])
    
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.info("Real-time flight tracking using OpenSky Network API")

# Main content
st.title("✈️ Real-Time Global Flight Analytics")
st.markdown("Live airspace monitoring with advanced analytics")

# Load data
@st.cache_data(ttl=60)
def load_data(region):
    df_raw = pipeline.collect_live_states(region)
    df = pipeline.transform_states(df_raw)
    return df

try:
    with st.spinner('Loading flight data...'):
        df = load_data(region)
    
    if df.empty:
        st.warning("No flight data available")
        st.stop()
    
    # Apply filters
    df_filtered = df.copy()
    if aircraft_filter == 'light':
        df_filtered = df_filtered[df_filtered['category'] == 2]
    elif aircraft_filter == 'small':
        df_filtered = df_filtered[df_filtered['category'] == 3]
    elif aircraft_filter == 'large':
        df_filtered = df_filtered[df_filtered['category'].isin([4, 5])]
    elif aircraft_filter == 'heavy':
        df_filtered = df_filtered[df_filtered['category'] == 6]
    
    # Update country filter
    countries = ['all'] + sorted(df['origin_country'].unique().tolist())
    country_filter = st.sidebar.selectbox("Country Focus", countries)
    
    if country_filter != 'all':
        df_filtered = df_filtered[df_filtered['origin_country'] == country_filter]
    
    # KPIs
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Active Flights", f"{len(df):,}")
    with col2:
        st.metric("Filtered", f"{len(df_filtered):,}")
    with col3:
        st.metric("Countries", df_filtered['origin_country'].nunique())
    with col4:
        st.metric("Avg Altitude", f"{df_filtered['altitude_ft'].mean():,.0f} ft")
    with col5:
        st.metric("Avg Speed", f"{df_filtered['speed_knots'].mean():,.0f} kts")
    with col6:
        climbing = len(df_filtered[df_filtered['vertical_rate'] > 2.5])
        st.metric("Climbing", climbing)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Live Map", "📊 Analytics", "🔍 Search", "📈 Insights"])
    
    with tab1:
        st.subheader("Live Flight Map")
        
        fig = px.scatter_mapbox(
            df_filtered,
            lat='latitude',
            lon='longitude',
            hover_name='callsign',
            hover_data=['altitude_ft', 'speed_knots', 'origin_country', 'aircraft_type'],
            color='altitude_category',
            size='speed_knots',
            size_max=12,
            color_discrete_map={
                'Low': '#3498db',
                'Medium': '#2ecc71',
                'High': '#f39c12',
                'Very High': '#e74c3c',
                'Extreme': '#9b59b6'
            },
            zoom=3.5,
            height=600,
        )
        
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Analytics Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Country distribution
            country_counts = df_filtered['origin_country'].value_counts().head(10)
            fig = px.bar(
                x=country_counts.values,
                y=country_counts.index,
                orientation='h',
                title="Top 10 Countries",
                labels={'x': 'Flights', 'y': 'Country'},
                color=country_counts.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Altitude distribution
            fig = px.histogram(
                df_filtered,
                x='altitude_ft',
                nbins=40,
                title="Altitude Distribution",
                labels={'altitude_ft': 'Altitude (feet)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Aircraft types
            type_counts = df_filtered['aircraft_type'].value_counts().head(8)
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Aircraft Types",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Speed vs Altitude
            fig = px.scatter(
                df_filtered.sample(min(500, len(df_filtered))),
                x='altitude_ft',
                y='speed_knots',
                color='aircraft_type',
                title="Speed vs Altitude",
                opacity=0.6
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Aircraft Search")
        
        search = st.text_input("Search by callsign", placeholder="e.g. UAL123")
        
        if search:
            results = df_filtered[df_filtered['callsign'].str.contains(search.upper(), na=False)]
            st.write(f"Found {len(results)} aircraft")
            if len(results) > 0:
                st.dataframe(
                    results[['callsign', 'origin_country', 'aircraft_type', 'altitude_ft', 'speed_knots']],
                    use_container_width=True
                )
        else:
            st.dataframe(
                df_filtered[['callsign', 'origin_country', 'aircraft_type', 'altitude_ft', 'speed_knots']].head(50),
                use_container_width=True
            )
    
    with tab4:
        st.subheader("Key Insights")
        
        # Top country
        top_country = df_filtered['origin_country'].value_counts().iloc[0]
        top_count = df_filtered['origin_country'].value_counts().values[0]
        st.info(f"🌍 Most Active: **{top_country}** with **{top_count}** flights")
        
        # Highest/Fastest
        highest = df_filtered.loc[df_filtered['altitude_ft'].idxmax()]
        fastest = df_filtered.loc[df_filtered['speed_knots'].idxmax()]
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🚀 Highest: **{highest['callsign']}** at **{highest['altitude_ft']:,.0f} ft**")
        with col2:
            st.warning(f"⚡ Fastest: **{fastest['callsign']}** at **{fastest['speed_knots']:,.0f} kts**")
        
        # Traffic density
        density = len(df_filtered) / 100
        st.metric("Traffic Density", f"{density:.1f} flights per 1000 sq degrees")

    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data from OpenSky Network")

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Try refreshing the page")