import requests
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenSkyClient:
    """Client for OpenSky Network API with OAuth2 authentication"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
        self.api_base = "https://opensky-network.org/api"
        self.access_token = None
        self.token_expires_at = None
        
    def _get_access_token(self) -> str:
        """Obtain OAuth2 access token"""
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.access_token
            
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(self.auth_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        # Token expires in 30 minutes, refresh 5 minutes early
        self.token_expires_at = time.time() + token_data.get("expires_in", 1800) - 300
        
        logger.info("Successfully obtained access token")
        return self.access_token
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated API request"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        url = f"{self.api_base}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        
        # Check rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-Rate-Limit-Retry-After-Seconds', 60))
            logger.warning(f"Rate limited. Retry after {retry_after} seconds")
            raise Exception(f"Rate limited. Retry after {retry_after} seconds")
        
        response.raise_for_status()
        return response.json()
    
    def get_states(self, 
                   time_secs: Optional[int] = None,
                   icao24: Optional[List[str]] = None,
                   bbox: Optional[Dict[str, float]] = None,
                   extended: int = 1) -> pd.DataFrame:
        """
        Get current state vectors for all aircraft
        
        Args:
            time_secs: Unix timestamp (optional)
            icao24: List of ICAO24 addresses to filter (optional)
            bbox: Bounding box dict with lamin, lamax, lomin, lomax (optional)
            extended: Set to 1 to get aircraft category (default: 1)
        """
        params = {'extended': extended}
        
        if time_secs:
            params['time'] = time_secs
        
        if icao24:
            params['icao24'] = icao24
        
        if bbox:
            params.update(bbox)
        
        data = self._make_request("/states/all", params)
        
        if not data.get('states'):
            return pd.DataFrame()
        
        # Check how many columns we actually got
        first_row = data['states'][0] if data['states'] else []
        num_columns = len(first_row)
        
        logger.info(f"Received {num_columns} columns from API (extended={extended})")
        
        # Column names for state vectors (18 columns WITH extended=1)
        columns = [
            'icao24', 'callsign', 'origin_country', 'time_position',
            'last_contact', 'longitude', 'latitude', 'baro_altitude',
            'on_ground', 'velocity', 'true_track', 'vertical_rate',
            'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
        ]
        
        # If we have 18 columns, the last one is category
        if num_columns == 18:
            columns.append('category')
            logger.info("Category column included!")
        else:
            logger.warning(f"Expected 18 columns with extended=1, got {num_columns}")
        
        df = pd.DataFrame(data['states'], columns=columns[:num_columns])
        df['request_time'] = data['time']
        df['request_datetime'] = pd.to_datetime(df['request_time'], unit='s')
        
        # Clean data types
        df['callsign'] = df['callsign'].str.strip()
        df['on_ground'] = df['on_ground'].astype(bool)
        
        # Add default category if not present
        if 'category' not in df.columns:
            logger.warning("Category column missing! Adding default category=0")
            df['category'] = 0
        
        return df
    
    def get_flights_interval(self, begin: int, end: int) -> pd.DataFrame:
        """Get all flights in time interval"""
        params = {'begin': begin, 'end': end}
        
        try:
            data = self._make_request("/flights/all", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting flights: {e}")
            return pd.DataFrame()
    
    def get_arrivals(self, airport: str, begin: int, end: int) -> pd.DataFrame:
        """Get arrivals for specific airport"""
        params = {'airport': airport, 'begin': begin, 'end': end}
        
        try:
            data = self._make_request("/flights/arrival", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting arrivals: {e}")
            return pd.DataFrame()
    
    def get_departures(self, airport: str, begin: int, end: int) -> pd.DataFrame:
        """Get departures for specific airport"""
        params = {'airport': airport, 'begin': begin, 'end': end}
        
        try:
            data = self._make_request("/flights/departure", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting departures: {e}")
            return pd.DataFrame()