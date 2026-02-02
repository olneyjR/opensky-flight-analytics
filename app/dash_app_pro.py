import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import json

from src.api.opensky_client import OpenSkyClient
from src.etl.data_pipeline import FlightDataPipeline
from config.config import Config

# Initialize
config = Config()
client = OpenSkyClient(config.OPENSKY_CLIENT_ID, config.OPENSKY_CLIENT_SECRET)
pipeline = FlightDataPipeline(client)

# Create Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    title="OpenSky Flight Analytics Pro"
)

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
                {'label': 'Commercial Only', 'value': 'commercial'},
                {'label': 'Private Only', 'value': 'private'},
                {'label': 'Heavy Aircraft', 'value': 'heavy'},
                {'label': 'High Altitude (>30k ft)', 'value': 'high_alt'}
            ],
            value='all',
            className="mb-3"
        ),
        
        html.Label("Country Focus", className="text-white"),
        dcc.Dropdown(
            id='country-filter',
            options=[{'label': 'All Countries', 'value': 'all'}],
            value='all',
            className="mb-3"
        ),
        
        html.Hr(),
        
        dbc.Button([html.I(className="fas fa-sync-alt me-2"), "Refresh Data"], 
                   id="refresh-button", color="primary", className="w-100 mb-2"),
        dbc.Button([html.I(className="fas fa-download me-2"), "Export CSV"], 
                   id="export-button", color="success", className="w-100 mb-2"),
        
        html.Hr(),
        
        html.Div([
            html.H6("Search Aircraft", className="text-white"),
            dbc.Input(id="callsign-search", placeholder="Enter callsign...", className="mb-2"),
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
    'width': '280px',
    'padding': '0',
    'background-color': '#1e2130'
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
                        html.H6("Active Flights", className="text-muted"),
                        html.H3(id="total-flights", children="0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-globe fa-2x text-success mb-2"),
                        html.H6("Countries", className="text-muted"),
                        html.H3(id="total-countries", children="0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-arrow-up fa-2x text-warning mb-2"),
                        html.H6("Avg Altitude", className="text-muted"),
                        html.H3(id="avg-altitude", children="0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-tachometer-alt fa-2x text-danger mb-2"),
                        html.H6("Avg Speed", className="text-muted"),
                        html.H3(id="avg-speed", children="0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle fa-2x text-info mb-2"),
                        html.H6("Anomalies", className="text-muted"),
                        html.H3(id="anomaly-count", children="0")
                    ], className="text-center")
                ])
            ])
        ], width=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-line fa-2x text-purple mb-2"),
                        html.H6("Density Score", className="text-muted"),
                        html.H3(id="density-score", children="0")
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
        dbc.Tab(label="⚠️ Anomalies", tab_id="tab-anomalies"),
        dbc.Tab(label="📈 Insights", tab_id="tab-insights"),
    ], id="tabs", active_tab="tab-map"),
    
    html.Div(id="tab-content", className="mt-3"),
    
    # Hidden components
    dcc.Store(id='flight-data'),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    dcc.Download(id="download-csv")
    
], style={'marginLeft': '300px', 'padding': '20px'})

app.layout = html.Div([sidebar, content])


# Callbacks
@app.callback(
    [Output('flight-data', 'data'),
     Output('total-flights', 'children'),
     Output('total-countries', 'children'),
     Output('avg-altitude', 'children'),
     Output('avg-speed', 'children'),
     Output('anomaly-count', 'children'),
     Output('density-score', 'children'),
     Output('country-filter', 'options'),
     Output('last-update', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')],
    [State('region-dropdown', 'value')]
)
def update_data(n_clicks, n_intervals, region):
    """Fetch and update flight data"""
    try:
        df_raw = pipeline.collect_live_states(region)
        df = pipeline.transform_states(df_raw)
        metrics = pipeline.aggregate_metrics(df)
        
        if df.empty:
            return None, "0", "0", "0 ft", "0 kts", "0", "0", [{'label': 'All Countries', 'value': 'all'}], "No data"
        
        # Calculate anomalies
        anomalies = 0
        if len(df) > 0:
            # High speed anomalies
            anomalies += len(df[df['speed_knots'] > 600])
            # Low altitude commercial
            anomalies += len(df[(df['altitude_ft'] < 5000) & (df['category'].isin([3,4,5,6]))])
        
        # Density score (flights per 1000 sq degrees)
        density = len(df) / 100
        
        # Country options for filter
        countries = [{'label': 'All Countries', 'value': 'all'}]
        countries.extend([
            {'label': c, 'value': c} 
            for c in sorted(df['origin_country'].unique())
        ])
        
        data_json = df.to_json(date_format='iso', orient='split')
        update_time = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        
        return (
            data_json,
            f"{metrics.get('total_flights', 0):,}",
            f"{metrics.get('countries', 0)}",
            f"{metrics.get('avg_altitude_ft', 0):,.0f} ft",
            f"{metrics.get('avg_speed_knots', 0):,.0f} kts",
            f"{anomalies}",
            f"{density:.1f}",
            countries,
            update_time
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, "Error", "Error", "Error", "Error", "Error", "Error", [{'label': 'All', 'value': 'all'}], "Error"


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('flight-data', 'data'),
     Input('aircraft-filter', 'value'),
     Input('country-filter', 'value')]
)
def render_tab(active_tab, data_json, aircraft_filter, country_filter):
    """Render tab content"""
    if not data_json:
        return dbc.Alert("Click 'Refresh Data' to load flight information", color="info")
    
    df = pd.read_json(data_json, orient='split')
    
    # Apply filters
    if aircraft_filter == 'commercial':
        df = df[df['category'].isin([3, 4, 5, 6])]
    elif aircraft_filter == 'private':
        df = df[df['category'] == 2]
    elif aircraft_filter == 'heavy':
        df = df[df['category'] == 6]
    elif aircraft_filter == 'high_alt':
        df = df[df['altitude_ft'] > 30000]
    
    if country_filter != 'all':
        df = df[df['origin_country'] == country_filter]
    
    if active_tab == "tab-map":
        return render_map_tab(df)
    elif active_tab == "tab-analytics":
        return render_analytics_tab(df)
    elif active_tab == "tab-search":
        return render_search_tab(df)
    elif active_tab == "tab-anomalies":
        return render_anomalies_tab(df)
    elif active_tab == "tab-insights":
        return render_insights_tab(df)


def render_map_tab(df):
    """Live flight map"""
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
            'latitude': ':.3f',
            'longitude': ':.3f'
        },
        color='altitude_category',
        size='speed_knots',
        size_max=15,
        color_discrete_map={
            'Low': '#3498db',
            'Medium': '#2ecc71',
            'High': '#f39c12',
            'Very High': '#e74c3c',
            'Extreme': '#9b59b6'
        },
        zoom=3,
        height=700,
    )
    
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    return dcc.Graph(figure=fig)


def render_analytics_tab(df):
    """Analytics dashboard"""
    row1 = dbc.Row([
        dbc.Col([
            dcc.Graph(figure=create_country_bar(df))
        ], width=6),
        dbc.Col([
            dcc.Graph(figure=create_altitude_dist(df))
        ], width=6)
    ])
    
    row2 = dbc.Row([
        dbc.Col([
            dcc.Graph(figure=create_speed_box(df))
        ], width=6),
        dbc.Col([
            dcc.Graph(figure=create_aircraft_pie(df))
        ], width=6)
    ])
    
    return html.Div([row1, row2])


def render_search_tab(df):
    """Aircraft search table"""
    display_cols = ['callsign', 'origin_country', 'aircraft_type', 'altitude_ft', 'speed_knots', 'latitude', 'longitude']
    
    return dash_table.DataTable(
        data=df[display_cols].round(2).to_dict('records'),
        columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in display_cols],
        filter_action="native",
        sort_action="native",
        page_size=20,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#2e3442', 'fontWeight': 'bold'},
        style_data={'backgroundColor': '#1e2130', 'color': 'white'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#252a3a'}
        ]
    )


def render_anomalies_tab(df):
    """Detect and display anomalies"""
    anomalies = []
    
    # High speed
    high_speed = df[df['speed_knots'] > 600]
    if len(high_speed) > 0:
        anomalies.append(html.Div([
            html.H5("⚡ High Speed Aircraft (>600 kts)"),
            dash_table.DataTable(
                data=high_speed[['callsign', 'speed_knots', 'altitude_ft', 'origin_country']].to_dict('records'),
                columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in ['callsign', 'speed_knots', 'altitude_ft', 'origin_country']],
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': '#2e3442'},
                style_data={'backgroundColor': '#1e2130', 'color': 'white'}
            )
        ], className="mb-4"))
    
    # Low altitude commercial
    low_alt = df[(df['altitude_ft'] < 5000) & (df['category'].isin([3,4,5,6]))]
    if len(low_alt) > 0:
        anomalies.append(html.Div([
            html.H5("⬇️ Low Altitude Commercial (<5000 ft)"),
            dash_table.DataTable(
                data=low_alt[['callsign', 'altitude_ft', 'speed_knots', 'origin_country']].to_dict('records'),
                columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in ['callsign', 'altitude_ft', 'speed_knots', 'origin_country']],
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': '#2e3442'},
                style_data={'backgroundColor': '#1e2130', 'color': 'white'}
            )
        ], className="mb-4"))
    
    if not anomalies:
        return dbc.Alert("No anomalies detected", color="success")
    
    return html.Div(anomalies)


def render_insights_tab(df):
    """Key insights"""
    insights = []
    
    # Busiest country
    top_country = df['origin_country'].value_counts().index[0]
    top_count = df['origin_country'].value_counts().values[0]
    insights.append(f"🌍 Most Active: {top_country} with {top_count} flights")
    
    # Highest aircraft
    if 'altitude_ft' in df.columns and len(df) > 0:
        highest = df.loc[df['altitude_ft'].idxmax()]
        insights.append(f"🚀 Highest: {highest['callsign']} at {highest['altitude_ft']:,.0f} ft")
    
    # Fastest aircraft
    if 'speed_knots' in df.columns and len(df) > 0:
        fastest = df.loc[df['speed_knots'].idxmax()]
        insights.append(f"⚡ Fastest: {fastest['callsign']} at {fastest['speed_knots']:,.0f} kts")
    
    # Traffic density
    density = len(df) / 100
    insights.append(f"📊 Traffic Density: {density:.1f} flights per 1000 sq degrees")
    
    cards = [
        dbc.Card([
            dbc.CardBody([html.H5(insight, className="text-center")])
        ], className="mb-3")
        for insight in insights
    ]
    
    return html.Div(cards)


# Helper chart functions
def create_country_bar(df):
    country_counts = df['origin_country'].value_counts().head(10)
    fig = px.bar(x=country_counts.values, y=country_counts.index, orientation='h',
                 title="Top 10 Countries", color=country_counts.values, color_continuous_scale='Viridis')
    fig.update_layout(showlegend=False, height=400)
    return fig

def create_altitude_dist(df):
    fig = px.histogram(df, x='altitude_ft', nbins=50, title="Altitude Distribution",
                       color_discrete_sequence=['#3498db'])
    fig.update_layout(height=400)
    return fig

def create_speed_box(df):
    fig = px.box(df, x='altitude_category', y='speed_knots', title="Speed by Altitude",
                 color='altitude_category')
    fig.update_layout(showlegend=False, height=400)
    return fig

def create_aircraft_pie(df):
    type_counts = df['aircraft_type'].value_counts()
    fig = px.pie(values=type_counts.values, names=type_counts.index, 
                 title="Aircraft Types", hole=0.4)
    fig.update_layout(height=400)
    return fig


@app.callback(
    Output("download-csv", "data"),
    Input("export-button", "n_clicks"),
    State('flight-data', 'data'),
    prevent_initial_call=True
)
def export_csv(n_clicks, data_json):
    """Export data to CSV"""
    if data_json:
        df = pd.read_json(data_json, orient='split')
        return dcc.send_data_frame(df.to_csv, f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)


@app.callback(
    Output("search-results", "children"),
    Input("callsign-search", "value"),
    State('flight-data', 'data')
)
def search_aircraft(search_term, data_json):
    """Search for specific aircraft"""
    if not search_term or not data_json:
        return ""
    
    df = pd.read_json(data_json, orient='split')
    results = df[df['callsign'].str.contains(search_term.upper(), na=False)]
    
    if len(results) == 0:
        return "No aircraft found"
    
    return html.Div([
        html.P(f"Found {len(results)} aircraft:", className="mb-1"),
        html.Ul([html.Li(f"{row['callsign']} - {row['origin_country']}") for _, row in results.head(5).iterrows()])
    ])


if __name__ == '__main__':
    print("\n🌐 Starting OpenSky Flight Analytics Pro on http://localhost:8050")
    print("   Press Ctrl+C to stop\n")
    app.run_server(debug=True, host='0.0.0.0', port=8050)