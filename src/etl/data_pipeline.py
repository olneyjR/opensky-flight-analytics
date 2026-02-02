import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlightDataPipeline:
    """ETL pipeline for flight data"""
    
    def __init__(self, client):
        self.client = client
        from config.config import Config
        self.config = Config()
        
    def collect_live_states(self, region: str = "north_america") -> pd.DataFrame:
        """Collect live flight states for a region"""
        bbox = self.config.REGIONS.get(region)
        
        if not bbox:
            raise ValueError(f"Unknown region: {region}")
        
        logger.info(f"Collecting live states for {region}")
        df = self.client.get_states(bbox=bbox)
        
        if not df.empty:
            # Save raw data
            os.makedirs(self.config.RAW_DATA_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                self.config.RAW_DATA_DIR,
                f"states_{region}_{timestamp}.parquet"
            )
            df.to_parquet(filepath, index=False)
            logger.info(f"Saved {len(df)} states to {filepath}")
        
        return df
    
    def collect_airport_traffic(self, airport: str, days_back: int = 1) -> Dict[str, pd.DataFrame]:
        """Collect arrivals and departures for an airport"""
        end_time = int(datetime.now().timestamp())
        begin_time = end_time - (days_back * 86400)
        
        logger.info(f"Collecting traffic for {airport}")
        
        arrivals = self.client.get_arrivals(airport, begin_time, end_time)
        departures = self.client.get_departures(airport, begin_time, end_time)
        
        return {
            'arrivals': arrivals,
            'departures': departures
        }
    
    def transform_states(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform and enrich state vectors"""
        if df.empty:
            return df
        
        # Remove aircraft on ground for airborne analysis
        df_airborne = df[~df['on_ground']].copy()
        
        # Calculate derived metrics
        df_airborne['altitude_ft'] = df_airborne['baro_altitude'] * 3.28084  # meters to feet
        df_airborne['speed_knots'] = df_airborne['velocity'] * 1.94384  # m/s to knots
        
        # CRITICAL: Remove rows with NaN in essential columns
        df_airborne = df_airborne.dropna(subset=['latitude', 'longitude', 'velocity', 'baro_altitude'])
        
        # Fill any remaining NaN values
        df_airborne['speed_knots'] = df_airborne['speed_knots'].fillna(0).clip(lower=1)
        df_airborne['altitude_ft'] = df_airborne['altitude_ft'].fillna(0)
        
        # Categorize altitude
        df_airborne['altitude_category'] = pd.cut(
            df_airborne['altitude_ft'],
            bins=[0, 10000, 20000, 30000, 45000, 100000],
            labels=['Low', 'Medium', 'High', 'Very High', 'Extreme']
        )
        
        # Categorize speed
        df_airborne['speed_category'] = pd.cut(
            df_airborne['speed_knots'],
            bins=[0, 200, 350, 500, 1000],
            labels=['Slow', 'Medium', 'Fast', 'Very Fast']
        )
        
        # Aircraft type from category code - COMPLETE MAPPING
        aircraft_types = {
            0: 'No Info Available',
            1: 'No ADS-B Info', 
            2: 'Light (<15.5k lbs)',
            3: 'Small (15.5k-75k lbs)',
            4: 'Large (75k-300k lbs)',
            5: 'High Vortex Large (B-757)',
            6: 'Heavy (>300k lbs)',
            7: 'High Performance',
            8: 'Rotorcraft',
            9: 'Glider',
            10: 'Lighter-than-air',
            11: 'Parachutist',
            12: 'Ultralight',
            13: 'Reserved',
            14: 'UAV',
            15: 'Space Vehicle',
            16: 'Emergency Vehicle',
            17: 'Service Vehicle',
            18: 'Point Obstacle',
            19: 'Cluster Obstacle',
            20: 'Line Obstacle'
        }
        
        df_airborne['aircraft_type'] = df_airborne['category'].map(aircraft_types).fillna('Unknown')
        
        # Debug: print category distribution
        logger.info(f"Aircraft type distribution: {df_airborne['aircraft_type'].value_counts().to_dict()}")
    
        return df_airborne
    
    def aggregate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate aggregate metrics"""
        if df.empty:
            return {}
        
        metrics = {
            'total_flights': len(df),
            'countries': df['origin_country'].nunique(),
            'avg_altitude_ft': df['altitude_ft'].mean(),
            'avg_speed_knots': df['speed_knots'].mean(),
            'max_altitude_ft': df['altitude_ft'].max(),
            'max_speed_knots': df['speed_knots'].max(),
            'flights_by_country': df['origin_country'].value_counts().head(10).to_dict(),
            'flights_by_altitude': df['altitude_category'].value_counts().to_dict(),
            'flights_by_type': df['aircraft_type'].value_counts().to_dict(),
        }
        
        return metrics