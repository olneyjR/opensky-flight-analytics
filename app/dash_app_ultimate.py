import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from src.api.opensky_client import OpenSkyClient
from src.etl.data_pipeline import FlightDataPipeline
from config.config import Config

# Initialize
config = Config()
client = OpenSkyClient(config.OPENSKY_CLIENT_ID, config.OPENSKY_CLIENT_SECRET)
pipeline = FlightDataPipeline(client)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    title="OpenSky Ultimate Flight Analytics"
)

# Expose server for Gunicorn
server = app.server

# Sidebar
sidebar = html.Div([
    html.Div([
        html.H2("✈️ Flight Analytics", className="text-white"),
        html.Hr(),
        
        html.Label("Region", className="text-white"),
        dcc.Dropdown(
            id='region-dropdown',
            options=[
                {'label': '🇺🇸 North America', 'value': 'north_america'},
                {'label': '🇪🇺 Europe', 'value': 'europe'},
                {'label': '🌏 Asia-Pacific', 'value': 'asia'}
            ],
            value='north_america',
            className="mb-3"
        ),
        
        html.Label("Aircraft Filter", className="text-white"),
        dcc.Dropdown(
            id='aircraft-filter',
            options=[
                {'label': 'All Aircraft', 'value': 'all'},
                {'label': 'Light (<15.5k lbs)', 'value': 'light'},
                {'label': 'Small (15.5k-75k lbs)', 'value': 'small'},
                {'label': 'Large (75k-300k lbs)', 'value': 'large'},
                {'label': 'Heavy (>300k lbs)', 'value': 'heavy'},
                {'label': 'High Performance', 'value': 'performance'},
                {'label': 'Rotorcraft', 'value': 'rotorcraft'},
            ],
            value='all',
            className="mb-3"
        ),
        
        html.Label("Country Focus (Origin)", className="text-white"),
        dcc.Dropdown(
            id='country-filter',
            options=[{'label': 'All Countries', 'value': 'all'}],
            value='all',
            className="mb-3"
        ),
        html.Small("Shows only aircraft registered in selected country", className="text-muted"),
        
        html.Hr(),
        
        html.Label("Map Display", className="text-white"),
        dcc.RadioItems(
            id='map-mode',
            options=[
                {'label': ' Standard', 'value': 'standard'},
                {'label': ' With Directions', 'value': 'directions'},
                {'label': ' Heatmap', 'value': 'heatmap'}
            ],
            value='standard',
            className="text-white",
            labelStyle={'display': 'block', 'margin': '5px 0'}
        ),
        
        html.Hr(),
        
        dbc.Button([html.I(className="fas fa-sync-alt me-2"), "Refresh Data"], 
                   id="refresh-button", color="primary", className="w-100 mb-2"),
        dbc.Button([html.I(className="fas fa-download me-2"), "Export CSV"], 
                   id="export-button", color="success", className="w-100 mb-2"),
        
        html.Hr(),
        
        html.Div([
            html.H6("Search Aircraft", className="text-white"),
            dbc.Input(id="callsign-search", placeholder="Enter callsign (e.g. UAL123)...", className="mb-2"),
            html.Div(id="search-results", className="text-white small")
        ]),
        
        html.Hr(),
        html.Div(id='last-update', className="text-muted small"),
        
    ], style={'padding': '20px'})
], style={
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '300px',
    'padding': '0',
    'background-color': '#1e2130',
    'overflow-y': 'auto'
})

# Main content
content = html.Div([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Real-Time Global Flight Tracking & Analytics"),
            html.P("Live airspace monitoring with advanced analytics and insights", className="text-muted")
        ])
    ], className="mb-4"),
    
    # KPI Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-plane fa-2x text-primary mb-2"),
                        html.H6("Active Flights", className="text-muted mb-0"),
                        html.H3(id="total-flights", children="0", className="mb-0"),
                        html.Small(id="filtered-count", className="text-muted")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-globe fa-2x text-success mb-2"),
                        html.H6("Countries", className="text-muted mb-0"),
                        html.H3(id="total-countries", children="0", className="mb-0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-arrow-up fa-2x text-warning mb-2"),
                        html.H6("Avg Altitude", className="text-muted mb-0"),
                        html.H3(id="avg-altitude", children="0", className="mb-0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-tachometer-alt fa-2x text-danger mb-2"),
                        html.H6("Avg Speed", className="text-muted mb-0"),
                        html.H3(id="avg-speed", children="0", className="mb-0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-arrow-circle-up fa-2x text-info mb-2"),
                        html.H6("Climbing", className="text-muted mb-0"),
                        html.H3(id="climbing-count", children="0", className="mb-0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-arrow-circle-down fa-2x text-purple mb-2"),
                        html.H6("Descending", className="text-muted mb-0"),
                        html.H3(id="descending-count", children="0", className="mb-0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
    ], className="mb-4"),
    
    # Tabs
    dbc.Tabs([
        dbc.Tab(label="🗺️ Live Map", tab_id="tab-map"),
        dbc.Tab(label="📊 Analytics", tab_id="tab-analytics"),
        dbc.Tab(label="🔍 Aircraft Search", tab_id="tab-search"),
        dbc.Tab(label="🧭 Traffic Flow", tab_id="tab-flow"),
        dbc.Tab(label="📈 Insights", tab_id="tab-insights"),
    ], id="tabs", active_tab="tab-map"),
    
    html.Div(id="tab-content", className="mt-3"),
    
    # Hidden components
    dcc.Store(id='flight-data'),
    dcc.Store(id='filtered-data'),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    dcc.Download(id="download-csv")
    
], style={'marginLeft': '320px', 'padding': '20px'})

app.layout = html.Div([sidebar, content])


# Callbacks
@app.callback(
    [Output('flight-data', 'data'),
     Output('country-filter', 'options'),
     Output('last-update', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')],
    [State('region-dropdown', 'value')]
)
def update_data(n_clicks, n_intervals, region):
    """Fetch flight data"""
    try:
        df_raw = pipeline.collect_live_states(region)
        df = pipeline.transform_states(df_raw)
        
        if df.empty:
            return None, [{'label': 'All Countries', 'value': 'all'}], "No data"
        
        # Country options
        countries = [{'label': 'All Countries', 'value': 'all'}]
        country_counts = df['origin_country'].value_counts()
        countries.extend([
            {'label': f"{c} ({country_counts[c]})", 'value': c} 
            for c in sorted(df['origin_country'].unique())
        ])
        
        data_json = df.to_json(date_format='iso', orient='split')
        update_time = f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(df):,} flights"
        
        return data_json, countries, update_time
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, [{'label': 'All', 'value': 'all'}], f"Error: {str(e)}"


@app.callback(
    [Output('filtered-data', 'data'),
     Output('total-flights', 'children'),
     Output('filtered-count', 'children'),
     Output('total-countries', 'children'),
     Output('avg-altitude', 'children'),
     Output('avg-speed', 'children'),
     Output('climbing-count', 'children'),
     Output('descending-count', 'children')],
    [Input('flight-data', 'data'),
     Input('aircraft-filter', 'value'),
     Input('country-filter', 'value')]
)
def filter_data(data_json, aircraft_filter, country_filter):
    """Apply filters and calculate metrics"""
    if not data_json:
        return None, "0", "", "0", "0 ft", "0 kts", "0", "0"
    
    df = pd.read_json(data_json, orient='split')
    total_flights = len(df)
    
    # Apply aircraft filter
    if aircraft_filter == 'light':
        df = df[df['category'] == 2]
    elif aircraft_filter == 'small':
        df = df[df['category'] == 3]
    elif aircraft_filter == 'large':
        df = df[df['category'].isin([4, 5])]
    elif aircraft_filter == 'heavy':
        df = df[df['category'] == 6]
    elif aircraft_filter == 'performance':
        df = df[df['category'] == 7]
    elif aircraft_filter == 'rotorcraft':
        df = df[df['category'] == 8]
    
    # Apply country filter
    if country_filter != 'all':
        df = df[df['origin_country'] == country_filter]
    
    # Calculate metrics
    filtered_count = f"({len(df):,} after filters)" if len(df) != total_flights else ""
    countries = df['origin_country'].nunique()
    avg_alt = f"{df['altitude_ft'].mean():,.0f} ft" if len(df) > 0 else "0 ft"
    avg_speed = f"{df['speed_knots'].mean():,.0f} kts" if len(df) > 0 else "0 kts"
    
    # Climbing/descending
    climbing = len(df[df['vertical_rate'] > 2.5]) if 'vertical_rate' in df.columns else 0
    descending = len(df[df['vertical_rate'] < -2.5]) if 'vertical_rate' in df.columns else 0
    
    filtered_json = df.to_json(date_format='iso', orient='split')
    
    return (
        filtered_json,
        f"{total_flights:,}",
        filtered_count,
        f"{countries}",
        avg_alt,
        avg_speed,
        f"{climbing}",
        f"{descending}"
    )


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('filtered-data', 'data'),
     Input('map-mode', 'value')]
)
def render_tab(active_tab, data_json, map_mode):
    """Render tab content"""
    if not data_json:
        return dbc.Alert("Click 'Refresh Data' to load flight information", color="info")
    
    df = pd.read_json(data_json, orient='split')
    
    if active_tab == "tab-map":
        return render_map_tab(df, map_mode)
    elif active_tab == "tab-analytics":
        return render_analytics_tab(df)
    elif active_tab == "tab-search":
        return render_search_tab(df)
    elif active_tab == "tab-flow":
        return render_flow_tab(df)
    elif active_tab == "tab-insights":
        return render_insights_tab(df)


def render_map_tab(df, map_mode):
    """Enhanced map with different modes"""
    
    if map_mode == 'heatmap':
        # Density heatmap
        fig = go.Figure(go.Densitymapbox(
            lat=df['latitude'],
            lon=df['longitude'],
            z=df['altitude_ft'],
            radius=10,
            colorscale='Jet',
            showscale=True,
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()), zoom=3),
            height=700,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    
    elif map_mode == 'directions':
        # Map with direction arrows
        fig = go.Figure()
        
        # Sample flights for performance (show max 500)
        df_sample = df.sample(min(500, len(df)))
        
        for _, row in df_sample.iterrows():
            # Calculate arrow endpoint based on heading
            if pd.notna(row['true_track']):
                heading_rad = np.radians(row['true_track'])
                # Arrow length based on speed
                length = 0.05 * (row['speed_knots'] / 500)
                
                end_lat = row['latitude'] + length * np.cos(heading_rad)
                end_lon = row['longitude'] + length * np.sin(heading_rad)
                
                # Add arrow
                fig.add_trace(go.Scattermapbox(
                    lat=[row['latitude'], end_lat],
                    lon=[row['longitude'], end_lon],
                    mode='lines',
                    line=dict(width=2, color='cyan'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Add points
        fig.add_trace(go.Scattermapbox(
            lat=df_sample['latitude'],
            lon=df_sample['longitude'],
            mode='markers',
            marker=dict(size=8, color='orange'),
            text=df_sample['callsign'],
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=False
        ))
        
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()), zoom=4),
            height=700,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    
    else:  # standard
        # Standard scatter map with clustering
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            hover_name='callsign',
            hover_data={
                'altitude_ft': ':.0f',
                'speed_knots': ':.0f',
                'origin_country': True,
                'aircraft_type': True,
                'vertical_rate': ':.1f',
                'latitude': ':.3f',
                'longitude': ':.3f'
            },
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
            height=700,
        )
        
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            margin={"r":0,"t":0,"l":0,"b":0},
            mapbox=dict(
                center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean())
            )
        )
    
    return dcc.Graph(figure=fig, config={'scrollZoom': True})


def render_analytics_tab(df):
    """Analytics dashboard"""
    row1 = dbc.Row([
        dbc.Col([dcc.Graph(figure=create_country_bar(df))], width=6),
        dbc.Col([dcc.Graph(figure=create_altitude_dist(df))], width=6)
    ])
    
    row2 = dbc.Row([
        dbc.Col([dcc.Graph(figure=create_speed_altitude_scatter(df))], width=6),
        dbc.Col([dcc.Graph(figure=create_aircraft_pie(df))], width=6)
    ])
    
    return html.Div([row1, row2])


def render_search_tab(df):
    """Aircraft search table with vertical rate"""
    display_cols = ['callsign', 'origin_country', 'aircraft_type', 'altitude_ft', 'speed_knots', 'vertical_rate', 'latitude', 'longitude']
    
    # Add climb/descent indicator
    if 'vertical_rate' in df.columns:
        df['status'] = df['vertical_rate'].apply(lambda x: 
            '⬆️ Climbing' if x > 2.5 else '⬇️ Descending' if x < -2.5 else '➡️ Level'
        )
        display_cols.insert(3, 'status')
    
    return dash_table.DataTable(
        data=df[display_cols].round(2).to_dict('records'),
        columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in display_cols],
        filter_action="native",
        sort_action="native",
        page_size=25,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#2e3442', 'fontWeight': 'bold', 'color': 'white'},
        style_data={'backgroundColor': '#1e2130', 'color': 'white'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#252a3a'},
            {'if': {'filter_query': '{status} = "⬆️ Climbing"', 'column_id': 'status'},
             'backgroundColor': '#27ae60', 'color': 'white'},
            {'if': {'filter_query': '{status} = "⬇️ Descending"', 'column_id': 'status'},
             'backgroundColor': '#e74c3c', 'color': 'white'}
        ]
    )


def render_flow_tab(df):
    """Traffic flow analysis"""
    if 'true_track' not in df.columns:
        return dbc.Alert("No heading data available", color="warning")
    
    # Direction bins
    df['direction'] = pd.cut(
        df['true_track'],
        bins=[0, 45, 90, 135, 180, 225, 270, 315, 360],
        labels=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    )
    
    direction_counts = df['direction'].value_counts().sort_index()
    
    fig = go.Figure(go.Barpolar(
        r=direction_counts.values,
        theta=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
        marker_color='cyan',
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8
    ))
    
    fig.update_layout(
        template=None,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, direction_counts.max()]),
            angularaxis=dict(direction='clockwise')
        ),
        title="Traffic Flow by Direction",
        height=600
    )
    
    return dcc.Graph(figure=fig)


def render_insights_tab(df):
    """Enhanced insights"""
    insights = []
    
    # Top countries
    top_country = df['origin_country'].value_counts().head(3)
    insights.append(html.H5("🌍 Most Active Countries:"))
    insights.append(html.Ul([html.Li(f"{country}: {count} flights") for country, count in top_country.items()]))
    
    # Altitude insights
    insights.append(html.H5("📏 Altitude Analysis:"))
    insights.append(html.Ul([
        html.Li(f"Highest: {df['altitude_ft'].max():,.0f} ft ({df.loc[df['altitude_ft'].idxmax(), 'callsign']})"),
        html.Li(f"Average: {df['altitude_ft'].mean():,.0f} ft"),
        html.Li(f"Median: {df['altitude_ft'].median():,.0f} ft")
    ]))
    
    # Speed insights
    insights.append(html.H5("⚡ Speed Analysis:"))
    insights.append(html.Ul([
        html.Li(f"Fastest: {df['speed_knots'].max():,.0f} kts ({df.loc[df['speed_knots'].idxmax(), 'callsign']})"),
        html.Li(f"Average: {df['speed_knots'].mean():,.0f} kts"),
        html.Li(f"Slowest: {df['speed_knots'].min():,.0f} kts")
    ]))
    
    # Aircraft types
    insights.append(html.H5("✈️ Aircraft Distribution:"))
    type_dist = df['aircraft_type'].value_counts().head(5)
    insights.append(html.Ul([html.Li(f"{atype}: {count}") for atype, count in type_dist.items()]))
    
    return html.Div(insights, style={'padding': '20px'})


# Chart helpers
def create_country_bar(df):
    country_counts = df['origin_country'].value_counts().head(15)
    fig = px.bar(
        x=country_counts.values, 
        y=country_counts.index, 
        orientation='h',
        title="Top 15 Countries by Flight Count",
        labels={'x': 'Flights', 'y': 'Country'},
        color=country_counts.values,
        color_continuous_scale='Viridis'
    )
    fig.update_layout(showlegend=False, height=500)
    return fig

def create_altitude_dist(df):
    fig = px.histogram(
        df, 
        x='altitude_ft', 
        nbins=40,
        title="Altitude Distribution",
        labels={'altitude_ft': 'Altitude (feet)'},
        color_discrete_sequence=['#3498db']
    )
    fig.update_layout(height=500)
    return fig

def create_speed_altitude_scatter(df):
    fig = px.scatter(
        df.sample(min(1000, len(df))),  # Sample for performance
        x='altitude_ft',
        y='speed_knots',
        color='aircraft_type',
        title="Speed vs Altitude",
        labels={'altitude_ft': 'Altitude (feet)', 'speed_knots': 'Speed (knots)'},
        opacity=0.6
    )
    fig.update_layout(height=500)
    return fig

def create_aircraft_pie(df):
    type_counts = df['aircraft_type'].value_counts().head(8)
    fig = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Aircraft Types",
        hole=0.4
    )
    fig.update_layout(height=500)
    return fig


@app.callback(
    Output("download-csv", "data"),
    Input("export-button", "n_clicks"),
    State('filtered-data', 'data'),
    prevent_initial_call=True
)
def export_csv(n_clicks, data_json):
    if data_json:
        df = pd.read_json(data_json, orient='split')
        return dcc.send_data_frame(
            df.to_csv, 
            f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            index=False
        )


@app.callback(
    Output("search-results", "children"),
    Input("callsign-search", "value"),
    State('flight-data', 'data')
)
def search_aircraft(search_term, data_json):
    if not search_term or not data_json:
        return ""
    
    df = pd.read_json(data_json, orient='split')
    results = df[df['callsign'].str.contains(search_term.upper(), na=False)]
    
    if len(results) == 0:
        return "No aircraft found"
    
    return html.Div([
        html.P(f"Found {len(results)} aircraft:", className="mb-1"),
        html.Ul([
            html.Li(f"{row['callsign']} - {row['origin_country']} - {row['altitude_ft']:,.0f} ft") 
            for _, row in results.head(10).iterrows()
        ])
    ])



if __name__ == '__main__':
    print("\n🌐 Starting OpenSky Ultimate Flight Analytics on http://localhost:8050")
    print("   Press Ctrl+C to stop\n")
    app.run_server(debug=True, host='0.0.0.0', port=8050)
