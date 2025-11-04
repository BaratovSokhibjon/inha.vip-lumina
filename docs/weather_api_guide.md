# API Integration Guide - Lumina Smart Home

## Overview

Lumina now uses a **hybrid dual-API strategy** for comprehensive environmental monitoring:

- **WAQI (World Air Quality Index)**: Air quality + Basic weather data
- **WeatherAPI.com**: Detailed weather forecasts and conditions
- **USGS**: Earthquake monitoring (already implemented)

---

## 🔑 Getting API Keys

### 1. WAQI API Key (Free - Unlimited Requests)

1. Visit: https://aqicn.org/data-platform/token/
2. Fill out the form with your details
3. You'll receive a token via email
4. Add to `.env`:
   ```bash
   WAQI_API_KEY=your_waqi_token_here
   WAQI_LOCATION=seoul  # or use geo:37.5665;126.9780
   ```

**Features:**
- Real-time air quality (AQI, PM2.5, PM10, O3, CO, NO2, SO2)
- Basic weather data (temperature, humidity, pressure, wind)
- Updates every 10-15 minutes
- **Unlimited requests** (respect 1000 req/sec limit)

### 2. WeatherAPI.com Key (Free - 1M calls/month)

1. Visit: https://www.weatherapi.com/signup.aspx
2. Sign up for free account
3. Copy your API key from dashboard
4. Add to `.env`:
   ```bash
   WEATHERAPI_KEY=your_weatherapi_key_here
   ```

**Features:**
- Current weather conditions
- 3-day weather forecast
- Precipitation data
- Wind speed and direction
- UV index
- Air quality included
- **1,000,000 calls/month FREE**

### 3. USGS Earthquake API (Free - No Key Required)

Already configured! No API key needed.

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ========================================
# WAQI Air Quality API
# ========================================
WAQI_API_KEY=your_waqi_token_here
WAQI_API_URL=https://api.waqi.info/feed
WAQI_LOCATION=seoul
AIR_QUALITY_CHECK_INTERVAL=600  # 10 minutes

# ========================================
# WeatherAPI.com
# ========================================
WEATHERAPI_KEY=your_weatherapi_key_here
WEATHERAPI_URL=http://api.weatherapi.com/v1
WEATHER_CHECK_INTERVAL=900  # 15 minutes

# ========================================
# Weather Data Source Strategy
# ========================================
# Options: 'waqi', 'weatherapi', 'hybrid'
WEATHER_DATA_SOURCE=hybrid
USE_WAQI_FOR_BASIC_WEATHER=true

# ========================================
# Location Settings
# ========================================
LOCATION_LAT=37.5665
LOCATION_LON=126.9780
LOCATION_CITY=Seoul
```

### Weather Data Source Strategies

#### 1. **Hybrid (RECOMMENDED)** ✨
```bash
WEATHER_DATA_SOURCE=hybrid
```
- Uses WAQI for basic weather (temperature, humidity, pressure, wind)
- Uses WeatherAPI.com for detailed forecasts and conditions
- Best data coverage with redundancy
- Optimizes API usage

#### 2. **WAQI Only**
```bash
WEATHER_DATA_SOURCE=waqi
```
- Uses only WAQI for both air quality and weather
- Saves WeatherAPI quota
- Limited to basic weather data (no forecasts)

#### 3. **WeatherAPI Only**
```bash
WEATHER_DATA_SOURCE=weatherapi
```
- Uses only WeatherAPI.com for weather
- Uses WAQI only for air quality
- More detailed weather data
- Uses more WeatherAPI quota

---

## 📊 Data Structure

### Air Quality Data (from WAQI)

```python
air_quality_data = {
    'source': 'waqi',
    'last_check': datetime,
    'aqi': 46,  # Air Quality Index
    'components': {
        'pm25': 46,   # Fine particles
        'pm10': 24,   # Coarse particles
        'o3': 27.3,   # Ozone
        'co': 1,      # Carbon monoxide
        'no2': 11,    # Nitrogen dioxide
        'so2': 3.6,   # Sulfur dioxide
    },
    'weather': {
        'temperature': 17,  # °C
        'humidity': 59,     # %
        'pressure': 1024,   # hPa
        'wind_speed': 1.5,  # m/s
    },
    'location': 'Shanghai',
    'city_url': 'https://aqicn.org/city/shanghai'
}
```

### Weather Data (from Hybrid/WeatherAPI)

```python
weather_data = {
    'source': 'hybrid',  # or 'waqi', 'weatherapi', 'openweathermap'
    'last_check': datetime,
    'temperature': 17.0,
    'feels_like': 15.5,
    'humidity': 59,
    'pressure': 1024,
    'wind_speed': 1.5,
    'wind_direction': 'NE',
    'condition': 'Partly cloudy',
    'precipitation_mm': 0.0,
    'uv_index': 3,
    'location': 'Seoul',
    'waqi_available': True,
    'weatherapi_available': True
}
```

---

## 🧪 Testing

### Test WAQI API

```bash
# Test with demo token
curl "https://api.waqi.info/feed/seoul/?token=demo"

# Test with your token
curl "https://api.waqi.info/feed/seoul/?token=YOUR_TOKEN"

# Test with coordinates
curl "https://api.waqi.info/feed/geo:37.5665;126.9780/?token=YOUR_TOKEN"
```

### Test WeatherAPI.com

```bash
# Test current weather + AQI
curl "http://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=37.5665,126.9780&aqi=yes"

# Test 3-day forecast
curl "http://api.weatherapi.com/v1/forecast.json?key=YOUR_KEY&q=Seoul&days=3&aqi=yes"
```

### Test USGS Earthquake API

```bash
curl "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
```

---

## 📈 API Usage Tracking

### Expected Usage (10-minute polling)

| API | Calls/Day | Calls/Month | Free Limit | % Used | Cost |
|-----|-----------|-------------|------------|--------|------|
| USGS Earthquake | 288 | 8,640 | Unlimited | 0% | $0 |
| WAQI Air Quality | 144 | 4,320 | Unlimited | 0% | $0 |
| WeatherAPI.com | 144 | 4,320 | 1,000,000 | 0.4% | $0 |

**Total Monthly Cost: $0** ✅

---

## 🎨 LED Color Responses

### Air Quality Colors (AQI-based)

| AQI Range | Level | Color | Effect |
|-----------|-------|-------|--------|
| 0-50 | Good | Green | Solid |
| 51-100 | Moderate | Yellow | Solid |
| 101-150 | Unhealthy | Orange | Solid |
| 151+ | Dangerous | Red | Pulse |

### Weather Condition Colors

| Condition | Color | Effect |
|-----------|-------|--------|
| Clear/Sunny | Warm White | Solid |
| Cloudy | Cool White | Solid |
| Rain | Blue | Wave |
| Storm | Purple | Flash |
| Snow | Cyan | Pulse |
| Fog | Dim White | Fade |

### Temperature Colors

| Temperature | Color | Description |
|------------|-------|-------------|
| < 18°C | Orange/Amber | Cold |
| 18-28°C | White | Comfortable |
| > 28°C | Cool Blue | Hot |

---

## 🔧 Troubleshooting

### Issue: "WAQI API key not configured"

**Solution:**
1. Get API key from https://aqicn.org/data-platform/token/
2. Add to `.env` file: `WAQI_API_KEY=your_token_here`
3. Restart Lumina

### Issue: "No weather data available from hybrid sources"

**Solutions:**
1. Check both API keys are configured
2. Verify location settings are correct
3. Try changing to single source: `WEATHER_DATA_SOURCE=weatherapi`
4. Check API rate limits haven't been exceeded

### Issue: "All API sources failed"

**Solutions:**
1. Check internet connectivity
2. Verify API keys are valid
3. Check API service status:
   - WAQI: https://waqi.info/
   - WeatherAPI: https://www.weatherapi.com/
   - USGS: https://earthquake.usgs.gov/

### Issue: "Location not found"

**Solutions:**
1. For WAQI, try using geo coordinates instead of city name:
   ```bash
   WAQI_LOCATION=geo:37.5665;126.9780
   ```
2. Verify latitude/longitude are correct in `.env`
3. Try different city names (English or local language)

---

## 📚 Database Schema

### Environmental Data Table

```sql
CREATE TABLE environmental_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_type TEXT NOT NULL,  -- 'aqi', 'temperature', 'earthquake'
    value REAL,               -- Main value (AQI, temp, magnitude)
    details TEXT,             -- JSON with additional data
    source TEXT,              -- 'waqi', 'weatherapi', 'hybrid', etc.
    location TEXT             -- Location name
);
```

### Query Examples

```python
# Get last 24 hours of air quality
db.get_air_quality_history(hours=24)

# Get last 24 hours of weather
db.get_weather_history(hours=24)

# Log air quality
db.log_air_quality_detailed(aqi_data)

# Log weather
db.log_weather_detailed(weather_data)
```

---

## 🚀 Quick Start

1. **Get API Keys**
   ```bash
   # WAQI: https://aqicn.org/data-platform/token/
   # WeatherAPI: https://www.weatherapi.com/signup.aspx
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

3. **Run Lumina**
   ```bash
   lumina run
   ```

4. **Monitor Status**
   ```bash
   # Check sensor status
   lumina status
   
   # View logs
   tail -f logs/lumina.log
   ```

---

## 📞 Support

- **WAQI Documentation**: https://aqicn.org/json-api/doc/
- **WeatherAPI Docs**: https://www.weatherapi.com/docs/
- **USGS Earthquake API**: https://earthquake.usgs.gov/fdsnws/event/1/

---

## 🎯 Next Steps

1. **Get API keys** from WAQI and WeatherAPI.com
2. **Configure** your `.env` file
3. **Test** with demo tokens first
4. **Deploy** to your Raspberry Pi
5. **Monitor** the logs for successful API calls
6. **Customize** LED colors and thresholds

Enjoy your enhanced Lumina smart home system! 🌟
