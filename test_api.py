#!/usr/bin/env python3
"""Quick test script for OpenSky API"""

from src.api.opensky_client import OpenSkyClient
from src.etl.data_pipeline import FlightDataPipeline
from config.config import Config

def main():
    print("🛩️  Testing OpenSky API Connection...\n")
    
    # Initialize
    config = Config()
    client = OpenSkyClient(
        config.OPENSKY_CLIENT_ID,
        config.OPENSKY_CLIENT_SECRET
    )
    
    # Test authentication
    print("1. Testing authentication...")
    try:
        token = client._get_access_token()
        print("   ✅ Authentication successful!\n")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}\n")
        return
    
    # Test getting states
    print("2. Fetching live flight data for North America...")
    try:
        bbox = config.REGIONS['north_america']
        df = client.get_states(bbox=bbox)
        
        if df.empty:
            print("   ⚠️  No flights found\n")
        else:
            print(f"   ✅ Found {len(df)} flights!\n")
            print("   Sample data:")
            print(df[['callsign', 'origin_country', 'latitude', 'longitude', 'baro_altitude']].head(10))
            print()
    except Exception as e:
        print(f"   ❌ Error fetching data: {e}\n")
        return
    
    # Test data pipeline
    print("3. Testing data transformation...")
    try:
        pipeline = FlightDataPipeline(client)
        df_transformed = pipeline.transform_states(df)
        metrics = pipeline.aggregate_metrics(df_transformed)
        
        print(f"   ✅ Transformation successful!")
        print(f"   📊 Metrics:")
        print(f"      - Total flights: {metrics.get('total_flights', 0)}")
        print(f"      - Countries: {metrics.get('countries', 0)}")
        print(f"      - Avg altitude: {metrics.get('avg_altitude_ft', 0):.0f} ft")
        print(f"      - Avg speed: {metrics.get('avg_speed_knots', 0):.0f} kts")
        print()
        
    except Exception as e:
        print(f"   ❌ Error in transformation: {e}\n")
        return
    
    print("✨ All tests passed! Ready to run the dashboard.\n")

if __name__ == "__main__":
    main()