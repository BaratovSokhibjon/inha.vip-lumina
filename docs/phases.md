📋 Complete Implementation Plan: WAQI + WeatherAPI Integration
🎯 Project Overview
Lumina Smart Home IoT System - Integrating dual-API strategy for comprehensive environmental monitoring:
- WAQI API: Air quality (AQI, PM2.5, PM10, O3, CO, NO2, SO2) + Basic weather (temperature, humidity, pressure, wind)
- WeatherAPI.com: Detailed weather (forecasts, conditions, precipitation, UV index)
- USGS: Earthquake monitoring (already implemented)
---
📊 Current State Analysis
Existing Implementation:
- ✅ Using OpenWeatherMap for both air quality and weather
- ✅ Sensor manager with callbacks for alerts
- ✅ Database logging for environmental data
- ✅ Environment-based configuration system
- ✅ Check intervals: Earthquake (5 min), Air Quality (10 min), Weather (15 min)
- ✅ LED color responses based on environmental conditions
Files to Modify:
1. src/lumina/automation/sensors.py - Core sensor management
2. src/lumina/config/settings.py - Configuration settings
3. .env.example - Environment variables template
4. src/lumina/database/database.py - Enhanced logging for new data
5. requirements.txt - No changes needed (already has requests)
---
🔧 Implementation Strategy
Architecture Decision: Dual-API with Intelligent Fallback
┌─────────────────────────────────────────────────────┐
│              Sensor Manager (5-15 min polling)      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ USGS         │  │ WAQI         │  │ Weather  │ │
│  │ Earthquake   │  │ Air Quality  │  │ API.com  │ │
│  │              │  │ + Basic Wx   │  │ Detailed │ │
│  │ 5 min        │  │ 10 min       │  │ 15 min   │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Weather Data Aggregator                     │   │
│  │ - Primary: WAQI basic weather              │   │
│  │ - Fallback: WeatherAPI if WAQI unavailable │   │
│  │ - Enhancement: WeatherAPI for forecasts    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Database Logger                             │   │
│  │ - Air quality history                       │   │
│  │ - Weather history                           │   │
│  │ - Earthquake alerts                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ LED Color Controller                        │   │
│  │ - AQI-based colors                          │   │
│  │ - Temperature-based colors                  │   │
│  │ - Alert animations                          │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
---
📝 Detailed Implementation Tasks
Phase 1: API Configuration (READ-ONLY ANALYSIS COMPLETE ✓)
Task 1.1: Update Environment Variables
- Add WAQI_API_KEY and WAQI_API_URL to .env.example
- Add WEATHERAPI_KEY and WEATHERAPI_URL to .env.example
- Remove or deprecate OPENWEATHER_API_KEY (optional: keep for backward compatibility)
- Add configuration flags:
  - USE_WAQI_FOR_WEATHER=true (use WAQI's weather data as primary)
  - WEATHER_DATA_SOURCE=hybrid (options: waqi, weatherapi, hybrid)
Task 1.2: Update Settings Class
- Add new API endpoints to Settings class in settings.py
- Add API key validation methods
- Add configuration for weather data source preference
- Keep backward compatibility with OpenWeatherMap
---
Phase 2: Sensor Manager Refactoring
Task 2.1: Create Weather Data Aggregator
- New method: _aggregate_weather_data(waqi_data, weatherapi_data)
- Logic: Merge data from both sources intelligently
- Priority: WAQI for real-time, WeatherAPI for forecasts
Task 2.2: Implement WAQI Air Quality Integration
- Replace check_air_quality() method
- New API endpoint: https://api.waqi.info/feed/{city}/?token={api_key}
- Parse WAQI response structure:
    {
    data: {
      aqi: 46,
      iaqi: {
        pm25: {v: 46},
        pm10: {v: 24},
        o3: {v: 27.3},
        co: {v: 1},
        no2: {v: 11},
        so2: {v: 3.6},
        t: {v: 17},      // Temperature (°C)
        h: {v: 59},      // Humidity (%)
        p: {v: 1024},    // Pressure (hPa)
        w: {v: 1.5}      // Wind speed (m/s)
      }
    }
  }
  
Task 2.3: Implement WeatherAPI.com Integration
- New method: check_weather_detailed()
- API endpoint: http://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}&aqi=yes
- Parse response for:
  - Current conditions (clear, rain, cloudy, etc.)
  - Precipitation data
  - Wind direction and speed
  - UV index
  - "Feels like" temperature
  - 3-day forecast (separate endpoint: /v1/forecast.json)
Task 2.4: Implement Hybrid Weather Method
- New method: check_weather_hybrid()
- Logic:
    1. Call WAQI API
  2. If WAQI has weather data (t, h, p, w):
     - Use WAQI for basic weather
  3. Call WeatherAPI for detailed data
  4. Merge data with WAQI as baseline
  5. Store aggregated result
  
Task 2.5: Update Data Storage Structure
self.air_quality_data = {
    'source': 'waqi',
    'aqi': int,
    'pm25': float,
    'pm10': float,
    'o3': float,
    'co': float,
    'no2': float,
    'so2': float,
    'location': str,
    'last_update': datetime
}
self.weather_data = {
    'source': 'hybrid',  # 'waqi', 'weatherapi', or 'hybrid'
    'temperature': float,
    'feels_like': float,
    'humidity': int,
    'pressure': int,
    'wind_speed': float,
    'wind_direction': str,
    'condition': str,  # 'Clear', 'Rain', 'Cloudy', etc.
    'precipitation_mm': float,
    'uv_index': int,
    'last_update': datetime,
    'waqi_available': bool,
    'weatherapi_available': bool
}
---
Phase 3: Database Schema Enhancement
Task 3.1: Update Environmental Data Table
- Add new columns for detailed air quality components
- Add weather source tracking
- Migration strategy (if needed)
Task 3.2: Add New Logging Methods
def log_air_quality_detailed(self, aqi_data: Dict)
def log_weather_detailed(self, weather_data: Dict)
def get_air_quality_history(self, hours: int = 24) -> List[Dict]
def get_weather_history(self, hours: int = 24) -> List[Dict]
---
Phase 4: Error Handling & Fallback Logic
Task 4.1: API Failure Handling
- WAQI fails → Use cached data + log warning
- WeatherAPI fails → Use WAQI weather data only
- Both fail → Use last known good data + alert user
Task 4.2: Data Validation
- Validate WAQI response structure
- Validate WeatherAPI response structure
- Handle missing fields gracefully
- Add data quality scoring
Task 4.3: Rate Limiting
- WAQI: No rate limit (but respect 1000 req/sec)
- WeatherAPI: Track monthly usage (1M limit)
- Add usage counter in database
- Warning at 80% usage
---
Phase 5: API Registration & Testing
Task 5.1: Get API Keys
1. WAQI API Key
   - Register at: https://aqicn.org/data-platform/token/
   - Free tier: Unlimited requests
   - Response time: < 200ms
2. WeatherAPI.com Key
   - Register at: https://www.weatherapi.com/signup.aspx
   - Free tier: 1,000,000 calls/month
   - Features: Current + 3-day forecast + Air quality
Task 5.2: Test API Endpoints
# Test WAQI (replace with your location)
curl "https://api.waqi.info/feed/tashkent/?token=YOUR_TOKEN"
# Test WeatherAPI
curl "http://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=41.2995,69.2401&aqi=yes"
---
Phase 6: Integration & Testing
Task 6.1: Unit Tests
- Test WAQI API parsing
- Test WeatherAPI parsing
- Test data aggregation logic
- Test fallback mechanisms
Task 6.2: Integration Tests
- Test full sensor monitoring loop
- Test database logging
- Test LED color responses
- Test alert callbacks
Task 6.3: System Tests
- Run 24-hour test with real polling
- Verify data consistency
- Check API usage tracking
- Monitor error rates
---
📦 File Structure
inha.vip-lumina/
├── src/lumina/automation/
│   └── sensors.py                    # Modified: New WAQI + WeatherAPI logic
├── src/lumina/config/
│   └── settings.py                   # Modified: New API configurations
├── src/lumina/database/
│   └── database.py                   # Modified: Enhanced logging
├── .env.example                      # Modified: New API keys
├── requirements.txt                  # No change needed
└── tests/                            # New: Unit tests
    ├── test_waqi_integration.py
    ├── test_weatherapi_integration.py
    └── test_sensor_manager.py
---
🚀 API Usage Estimates
Daily Polling (10-minute intervals = 144 calls/day):
| API | Calls/Day | Calls/Month | Free Limit | % Used |
|-----|-----------|-------------|------------|--------|
| USGS Earthquake | 288 | 8,640 | Unlimited | 0% |
| WAQI Air Quality | 144 | 4,320 | Unlimited | 0% |
| WeatherAPI.com | 144 | 4,320 | 1,000,000 | 0.4% |
Total Monthly Costs: $0 ✅
---
🎨 LED Color Response Enhancements
New Color Modes:
# Air Quality Modes (based on WAQI data)
- Good (AQI 0-50): Green
- Moderate (AQI 51-100): Yellow
- Unhealthy (AQI 101-150): Orange
- Dangerous (AQI 151+): Red + Pulse
# Weather Modes (based on WeatherAPI conditions)
- Clear/Sunny: Warm white
- Cloudy: Cool white
- Rain: Blue with wave effect
- Storm: Purple with flash effect
- Snow: Cyan pulse
- Fog: Dim white
# Temperature Modes (based on WAQI temperature)
- Cold (<18°C): Orange/Amber
- Comfortable (18-28°C): White
- Hot (>28°C): Cool blue
---
⚙️ Configuration Examples
Example .env Configuration:
# ========================================
# NEW API CONFIGURATIONS
# ========================================
# WAQI Air Quality API (Free - Unlimited)
WAQI_API_KEY=your_waqi_token_here
WAQI_API_URL=https://api.waqi.info/feed
WAQI_LOCATION=tashkent  # or use lat/lon: geo:41.2995;69.2401
# WeatherAPI.com (Free - 1M calls/month)
WEATHERAPI_KEY=your_weatherapi_key_here
WEATHERAPI_URL=http://api.weatherapi.com/v1
# Weather Data Source Strategy
# Options: 'waqi', 'weatherapi', 'hybrid'
WEATHER_DATA_SOURCE=hybrid
USE_WAQI_FOR_BASIC_WEATHER=true
# Check Intervals (seconds)
AIR_QUALITY_CHECK_INTERVAL=600   # 10 minutes
WEATHER_CHECK_INTERVAL=900       # 15 minutes
# ========================================
# DEPRECATED (Keep for backward compatibility)
# ========================================
# OPENWEATHER_API_KEY=legacy_key_here
---
🔍 Key Benefits of This Implementation
1. Cost Efficiency: 100% free for your usage patterns
2. Redundancy: Multiple data sources prevent single point of failure
3. Rich Data: Comprehensive air quality + detailed weather
4. Real-time Updates: WAQI updates every 10-15 minutes
5. Forecasting: 3-day weather predictions from WeatherAPI
6. Scalability: Easy to add more locations or sensors
7. Backward Compatible: Can keep OpenWeatherMap as fallback
---
📚 Next Steps After Implementation
1. Web Dashboard Enhancement: Display air quality components (PM2.5, PM10, O3, etc.)
2. Historical Analysis: Track AQI trends over time
3. Smart Alerts: 
   - "High pollution detected, closing windows recommended"
   - "Rain expected in 2 hours"
   - "UV index high, wear sunscreen"
4. ML Integration: Predict user preferences based on weather/AQI
5. Voice Notifications: Text-to-speech for important alerts