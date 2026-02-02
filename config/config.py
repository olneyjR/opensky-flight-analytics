import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenSky API credentials
    OPENSKY_CLIENT_ID = os.getenv('OPENSKY_CLIENT_ID', 'olneyjr2@gmail.com-api-client')
    OPENSKY_CLIENT_SECRET = os.getenv('OPENSKY_CLIENT_SECRET', 'jDFaaxpTEHfeokOKg68EveWx59tEVXke')
    
    # API endpoints
    OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    OPENSKY_API_BASE = "https://opensky-network.org/api"
    
    # Data storage
    DATA_DIR = "data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    
    # Cache settings
    CACHE_DURATION = 300  # 5 minutes
    
    # Bounding boxes for areas of interest
    REGIONS = {
        "north_america": {
            "lamin": 24.0,
            "lamax": 71.0,
            "lomin": -170.0,
            "lomax": -50.0
        },
        "europe": {
            "lamin": 36.0,
            "lamax": 71.0,
            "lomin": -10.0,
            "lomax": 40.0
        },
        "asia": {
            "lamin": -10.0,
            "lamax": 55.0,
            "lomin": 60.0,
            "lomax": 150.0
        }
    }
    
    # Major airports for analysis
    MAJOR_AIRPORTS = [
        "KJFK", "KLAX", "KORD", "KATL", "KDFW",  # US
        "EGLL", "LFPG", "EDDF", "EHAM", "LEMD",  # Europe
        "RJTT", "VHHH", "WSSS", "YSSY", "OMDB"   # Asia-Pacific
    ]