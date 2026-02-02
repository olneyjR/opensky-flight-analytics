# OpenSky Flight Analytics

Real-time global flight tracking and analytics platform powered by OpenSky Network API.

## Live Demo

**[View Live Application](https://opensky-flight-analytics.onrender.com)**

## Features

**Live Flight Map**
- Track thousands of aircraft in real-time across continents
- Color-coded altitude visualization
- Interactive hover data with aircraft details

**Advanced Analytics**
- Traffic patterns and density analysis
- Speed and altitude distributions
- Country-based statistics
- Aircraft type categorization

**Aircraft Search**
- Find specific flights by callsign instantly
- Filter by aircraft type, country, and altitude
- Real-time climb/descent indicators

**Traffic Flow Analysis**
- Directional pattern visualization
- Airspace density heatmaps
- Polar charts showing traffic flow

**Insights Dashboard**
- Key performance metrics
- Anomaly detection
- Highest/fastest aircraft tracking

**Data Export**
- Download flight data as CSV
- Full dataset export capabilities

## Map Display Modes

**Standard View**: Color-coded points showing altitude categories
**Direction Arrows**: Aircraft headings and flight path visualization  
**Heatmap**: Traffic density heat visualization

## Real-Time Metrics

- Active flights count with smart filtering
- Climbing and descending aircraft tracking
- Speed and altitude averages by region
- Country distribution analysis

## Aircraft Classification

Supports tracking of:
- Light aircraft (under 15,500 lbs)
- Small aircraft (15,500 - 75,000 lbs)
- Large aircraft (75,000 - 300,000 lbs)
- Heavy aircraft (over 300,000 lbs)
- High performance aircraft
- Rotorcraft

## Tech Stack

**Backend**
- Python 3.11
- Pandas and NumPy for data processing
- Custom ETL pipeline for data transformation
- OAuth2 authentication with OpenSky API

**Frontend**
- Dash (Plotly) for interactive visualizations
- Dash Bootstrap Components for responsive UI
- Plotly Express for charts and maps
- Custom CSS styling

**API Integration**
- OpenSky Network REST API
- Real-time state vector processing
- Authenticated requests with token management
- Rate limiting compliance

**Deployment**
- Render.com Platform-as-a-Service
- Gunicorn WSGI server
- Automatic HTTPS
- Environment variable management

## Data Sources

Flight data provided by OpenSky Network - a community-based receiver network which continuously collects air traffic surveillance data.

**Citation:**
Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic and Matthias Wilhelm.
"Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research".
In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), pages 83-94, April 2014.

## Local Development

### Prerequisites
- Python 3.11 or higher
- OpenSky Network API credentials
- Git

### Installation

Clone the repository:
```bash
git clone https://github.com/olneyjR/opensky-flight-analytics.git
cd opensky-flight-analytics
```

Create and activate virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenSky API credentials
```

Run the application:
```bash
python app/dash_app_ultimate.py
```

Visit `http://localhost:8050` in your browser.

## Project Structure
```
opensky-flight-analytics/
├── app/
│   └── dash_app_ultimate.py    # Main Dash application
├── src/
│   ├── api/
│   │   └── opensky_client.py   # OpenSky API client with OAuth2
│   ├── etl/
│   │   └── data_pipeline.py    # Data transformation pipeline
│   └── analysis/
│       └── flight_analytics.py # Analytics functions
├── config/
│   └── config.py               # Configuration settings
├── data/                       # Data storage (gitignored)
│   ├── raw/                    # Raw API responses
│   └── processed/              # Transformed datasets
├── requirements.txt            # Python dependencies
├── Procfile                    # Render deployment config
├── runtime.txt                 # Python version specification
└── README.md                   # Project documentation
```

## API Configuration

This project uses the OpenSky Network API. To run locally:

1. Create an account at [OpenSky Network](https://opensky-network.org/)
2. Navigate to your account settings
3. Generate API client credentials
4. Add credentials to `.env` file:
```
   OPENSKY_CLIENT_ID=your_client_id
   OPENSKY_CLIENT_SECRET=your_client_secret
```

### API Rate Limits

- Authenticated users: 4,000 API credits per day
- Each region query uses 1-4 credits based on geographic size
- Auto-refresh interval: 60 seconds (configurable)
- Unauthenticated users: 400 API credits per day

### API Endpoints Used

- `/states/all` - Retrieve all current aircraft state vectors
- `/flights/arrival` - Get arriving flights for specific airports
- `/flights/departure` - Get departing flights for specific airports
- `/flights/aircraft` - Historical flights for specific aircraft

## Use Cases

**Aviation Enthusiasts**
Track specific flights, monitor aircraft types, and analyze flight patterns in real-time.

**Research and Analysis**
Study air traffic patterns, airspace utilization, and flight dynamics using live data.

**Data Science Portfolio**
Demonstrate skills in API integration, data processing, real-time visualization, and full-stack development.

**Education**
Learn about air traffic control systems, ADS-B technology, and data engineering practices.

## Technical Highlights

**Data Pipeline Architecture**
- Real-time data collection from OpenSky API
- ETL pipeline with data validation and cleaning
- Efficient data transformation using Pandas
- Parquet file storage for historical analysis

**Performance Optimization**
- Client-side data caching
- Rate limit compliance and token management
- Efficient DataFrame operations
- Responsive UI with lazy loading

**Scalability Considerations**
- Modular architecture for easy extension
- Configurable refresh intervals
- Regional data filtering to reduce load
- Prepared for horizontal scaling

## Future Enhancements

- Historical flight replay functionality
- Airport-specific arrival and departure tracking
- Flight path prediction using machine learning
- Email and SMS alerts for specific aircraft
- Advanced filtering by airline and route
- 3D altitude visualization
- Mobile-responsive design improvements
- Real-time weather overlay integration
- Flight delay prediction models

## Author

**Jeffrey Olney**

Data professional specializing in full-stack analytics and data engineering. Over 10 years of experience bridging data infrastructure and analytical insight delivery.

**Technical Skills Demonstrated:**
- Full-stack data pipeline development
- RESTful API integration and authentication
- Real-time data processing and visualization
- Interactive dashboard development
- Cloud deployment and DevOps
- Python programming (Pandas, NumPy, Plotly)

**Contact:**
- LinkedIn: [linkedin.com/in/jeffrey-olney](https://www.linkedin.com/in/jeffrey-olney/)
- GitHub: [github.com/olneyjR](https://github.com/olneyjR)
- Email: olneyjr2@gmail.com

## Deployment

### Render.com Deployment

This application is deployed on Render.com using their free tier.

**Deployment Steps:**
1. Push code to GitHub repository
2. Connect Render.com to GitHub account
3. Create new Web Service
4. Configure environment variables
5. Deploy using Gunicorn WSGI server

**Configuration:**
- Runtime: Python 3.11.8
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app.dash_app_ultimate:server --bind 0.0.0.0:$PORT --timeout 120 --workers 2`

### Environment Variables Required
```
OPENSKY_CLIENT_ID=your_client_id
OPENSKY_CLIENT_SECRET=your_client_secret
```

## Performance Metrics

**Data Processing:**
- Processes 5,000+ aircraft state vectors per request
- Sub-second data transformation pipeline
- Real-time filtering and aggregation

**Visualization:**
- Interactive maps with 1,000+ simultaneous markers
- Multiple chart types with responsive rendering
- Smooth user interactions with optimized callbacks

**API Efficiency:**
- Token-based authentication with automatic refresh
- Request batching to minimize API calls
- Intelligent caching to reduce redundant requests

## License

This project is for educational and portfolio purposes. Flight data courtesy of OpenSky Network under their terms of service.

## Acknowledgments

**OpenSky Network** - For providing free, open access to air traffic data for research and educational purposes.

**Plotly/Dash** - For the excellent Python framework enabling rapid development of interactive analytical web applications.

## Contributing

This is a portfolio project, but suggestions and feedback are welcome. Please open an issue to discuss potential changes or improvements.

## Citation

If you use this project or its methodologies in your own work, please cite:
```
Olney, J. (2025). OpenSky Flight Analytics: Real-time Global Flight Tracking Platform.
GitHub repository: https://github.com/olneyjR/opensky-flight-analytics
```

## Support

For questions, issues, or feature requests, please open an issue on the GitHub repository or contact the author directly.

---

**Project Status:** Active Development | Last Updated: February 2025
