import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
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
    external_stylesheets=[dbc.themes.CYBORG],
    title="OpenSky Flight Analytics"
)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🛩️ Global Flight Analytics", className="text-center mb-4"),
            html.P("Real-time aircraft tracking powered by OpenSky Network", 
                   className="text-center text-muted")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Region Selection"),
                    dcc.Dropdown(
                        id='region-dropdown',
                        options=[
                            {'label': 'North America', 'value': 'north_america'},
                            {'label': 'Europe', 'value': 'europe'},
                            {'label': 'Asia-Pacific', 'value': 'asia'}
                        ],
                        value='north_america',
                        className="mb-3"
                    ),
                    dbc.Button("Refresh Data", id="refresh-button", color="primary", className="w-100")
                ])
            ], className="mb-4")
        ], width=3),
        
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Flights", className="text-muted"),
                            html.H3(id="total-flights", children="0")
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Countries", className="text-muted"),
                            html.H3(id="total-countries", children="0")
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Avg Altitude", className="text-muted"),
                            html.H3(id="avg-altitude", children="0 ft")
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Avg Speed", className="text-muted"),
                            html.H3(id="avg-speed", children="0 kts")
                        ])
                    ])
                ], width=3),
            ])
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Live Flight Map"),
                    dcc.Graph(id='flight-map', style={'height': '600px'})
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Flights by Country"),
                    dcc.Graph(id='country-chart')
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Altitude Distribution"),
                    dcc.Graph(id='altitude-chart')
                ])
            ])
        ], width=6),
    ]),
    
    dcc.Store(id='flight-data'),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0)  # Update every minute
    
], fluid=True)


@app.callback(
    [Output('flight-data', 'data'),
     Output('total-flights', 'children'),
     Output('total-countries', 'children'),
     Output('avg-altitude', 'children'),
     Output('avg-speed', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')],
    [State('region-dropdown', 'value')]
)
def update_data(n_clicks, n_intervals, region):
    """Fetch and update flight data"""
    try:
        # Collect and transform data
        df_raw = pipeline.collect_live_states(region)
        df = pipeline.transform_states(df_raw)
        metrics = pipeline.aggregate_metrics(df)
        
        if df.empty:
            return None, "0", "0", "0 ft", "0 kts"
        
        # Store data
        data_json = df.to_json(date_format='iso', orient='split')
        
        return (
            data_json,
            f"{metrics.get('total_flights', 0):,}",
            f"{metrics.get('countries', 0)}",
            f"{metrics.get('avg_altitude_ft', 0):,.0f} ft",
            f"{metrics.get('avg_speed_knots', 0):,.0f} kts"
        )
    except Exception as e:
        print(f"Error updating data: {e}")
        import traceback
        traceback.print_exc()
        return None, "Error", "Error", "Error", "Error"


@app.callback(
    Output('flight-map', 'figure'),
    Input('flight-data', 'data')
)
def update_map(data_json):
    """Update flight map visualization"""
    if not data_json:
        return go.Figure()
    
    df = pd.read_json(data_json, orient='split')
    
    # Create scatter mapbox
    fig = px.scatter_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        hover_name='callsign',
        hover_data={
            'altitude_ft': ':.0f',
            'speed_knots': ':.0f',
            'origin_country': True,
            'latitude': ':.2f',
            'longitude': ':.2f'
        },
        color='altitude_category',
        size='speed_knots',
        color_discrete_map={
            'Low': '#3498db',
            'Medium': '#2ecc71',
            'High': '#f39c12',
            'Very High': '#e74c3c',
            'Extreme': '#9b59b6'
        },
        zoom=3,
        height=600,
    )
    
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=True
    )
    
    return fig


@app.callback(
    Output('country-chart', 'figure'),
    Input('flight-data', 'data')
)
def update_country_chart(data_json):
    """Update country distribution chart"""
    if not data_json:
        return go.Figure()
    
    df = pd.read_json(data_json, orient='split')
    country_counts = df['origin_country'].value_counts().head(10)
    
    fig = px.bar(
        x=country_counts.values,
        y=country_counts.index,
        orientation='h',
        labels={'x': 'Number of Flights', 'y': 'Country'},
        color=country_counts.values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title="Number of Flights",
        yaxis_title="Country",
        height=400
    )
    
    return fig


@app.callback(
    Output('altitude-chart', 'figure'),
    Input('flight-data', 'data')
)
def update_altitude_chart(data_json):
    """Update altitude distribution chart"""
    if not data_json:
        return go.Figure()
    
    df = pd.read_json(data_json, orient='split')
    
    fig = px.histogram(
        df,
        x='altitude_ft',
        nbins=50,
        labels={'altitude_ft': 'Altitude (feet)'},
        color_discrete_sequence=['#3498db']
    )
    
    fig.update_layout(
        xaxis_title="Altitude (feet)",
        yaxis_title="Number of Flights",
        height=400
    )
    
    return fig


if __name__ == '__main__':
    print("\n🌐 Starting server on http://localhost:8050")
    print("   Press Ctrl+C to stop\n")
    app.run_server(debug=True, host='0.0.0.0', port=8050)