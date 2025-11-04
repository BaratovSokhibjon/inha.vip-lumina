"""
Sensor Manager for Lumina

This module handles all external API calls and environmental monitoring:
- Earthquake detection (USGS API)
- Air quality monitoring (OpenWeatherMap API)
- Weather/temperature monitoring (OpenWeatherMap API)
- Radio stations (Radio Browser API)
"""

import time
import threading
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

class SensorManager:
    """Independent sensor manager for environmental monitoring"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Data storage
        self.earthquake_data = []
        self.air_quality_data = {}
        self.weather_data = {}
        self.radio_stations = []

        # Last update times
        self.last_earthquake_check = 0
        self.last_air_quality_check = 0
        self.last_weather_check = 0

        # Callback functions for alerts
        self.earthquake_callback = None
        self.air_quality_callback = None
        self.temperature_callback = None

        # Threading control
        self.running = False
        self.monitor_thread = None

        # API settings from config
        self.api_timeout = getattr(config, 'API_TIMEOUT', 10)
        self.earthquake_check_interval = getattr(config, 'EARTHQUAKE_CHECK_INTERVAL', 300)
        self.earthquake_api_url = getattr(config, 'EARTHQUAKE_API_URL', 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson')
        self.earthquake_min_magnitude = getattr(config, 'EARTHQUAKE_MIN_MAGNITUDE', 5.5)
        self.air_quality_check_interval = getattr(config, 'AIR_QUALITY_CHECK_INTERVAL', 600)
        self.waqi_api_key = config.get('WAQI_API_KEY', '')
        self.weatherapi_key = config.get('WEATHERAPI_KEY', '')
        self.weatherapi_url = config.get('WEATHERAPI_URL', 'http://api.weatherapi.com/v1')
        self.logger.info(f"WeatherAPI key loaded: {'***' if self.weatherapi_key else 'NOT SET'}")
        self.logger.info(f"Config keys containing API: {[k for k in config.keys() if 'API' in k]}")
        self.weather_check_interval = getattr(config, 'WEATHER_CHECK_INTERVAL', 600)
        self.weather_api_url = getattr(config, 'WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5/weather')
        self.air_pollution_api_url = getattr(config, 'AIR_POLLUTION_API_URL', 'http://api.openweathermap.org/data/2.5/air_pollution')

        self.logger.info("Sensor manager initialized")

    def _make_api_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.api_timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            self.logger.error(f"API request timeout: {url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {url} - {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {url} - {e}")

        return None

    def check_earthquakes(self) -> List:
        """Check for significant earthquakes"""
        current_time = time.time()

        if current_time - self.last_earthquake_check < self.earthquake_check_interval:
            return self.earthquake_data

        try:
            data = self._make_api_request(self.earthquake_api_url)

            if not data or 'features' not in data:
                self.logger.warning("Invalid earthquake data received")
                return self.earthquake_data

            earthquakes = []
            for feature in data['features']:
                properties = feature['properties']
                magnitude = properties.get('mag', 0)

                if magnitude >= self.earthquake_min_magnitude:
                    earthquake = {
                        'magnitude': magnitude,
                        'place': properties.get('place', 'Unknown'),
                        'time': properties.get('time', 0) / 1000,  # Convert to seconds
                        'coordinates': feature['geometry']['coordinates'] if 'geometry' in feature else None
                    }
                    earthquakes.append(earthquake)

            self.earthquake_data = earthquakes
            self.last_earthquake_check = current_time
            self.logger.info(f"Earthquake check completed. Found {len(earthquakes)} significant earthquakes")
            return earthquakes

        except Exception as e:
            self.logger.error(f"Earthquake check failed: {e}")
            return []

    def check_air_quality(self) -> Dict:
        """Check air quality using WAQI API (with OpenWeatherMap fallback)"""
        current_time = time.time()

        if current_time - self.last_air_quality_check < self.air_quality_check_interval:
            return self.air_quality_data

        # Try WAQI first
        if self.waqi_api_key:
            try:
                self._check_air_quality_waqi()
                return self.air_quality_data
            except Exception as e:
                self.logger.warning(f"WAQI air quality check failed: {e}")

        # Fallback to OpenWeatherMap
        if self.config.get("api", {}).get("openweather_api_key"):
            try:
                self._check_air_quality_openweather()
                return self.air_quality_data
            except Exception as e:
                self.logger.warning(f"OpenWeatherMap air quality check failed: {e}")

        self.logger.error("All air quality API sources failed")
        return {}

    def check_weather(self) -> Dict:
        current_time = time.time()
        if current_time - self.last_weather_check < self.weather_check_interval:
            return self.weather_data
        strategy = self.config.get("api", {}).get("weather_data_source", "hybrid")
        if strategy == "hybrid":
            success = self._check_weather_hybrid()
        elif strategy == "weatherapi":
            success = self._check_weather_weatherapi()
        elif strategy == "openweathermap":
            success = self._check_weather_openweather()
        else:
            self.logger.error(f"Unknown weather data source: {strategy}")
            success = False
        if success:
            self.last_weather_check = current_time
        return self.weather_data if success else {}

    def _check_weather_weatherapi(self) -> bool:
        try:
            url = f"{self.weatherapi_url}/current.json"
            params = {
                'key': self.weatherapi_key,
                'q': f"{self.config['LOCATION_LAT']},{self.config['LOCATION_LON']}",
            }
            data = self._make_api_request(url, params)
            if not data or 'current' not in data:
                self.logger.warning("No weather data received from WeatherAPI")
                return False
            current = data['current']
            location = data.get('location', {})
            self.weather_data = {
                'source': 'weatherapi',
                'last_check': datetime.now(),
                'temperature': current.get('temp_c'),
                'feels_like': current.get('feelslike_c'),
                'humidity': current.get('humidity'),
                'pressure': current.get('pressure_mb'),
                'wind_speed': current.get('wind_kph', 0) / 3.6,  # Convert kph to m/s
                'wind_direction': current.get('wind_dir'),
                'condition': current.get('condition', {}).get('text', 'Unknown'),
                'precipitation_mm': current.get('precip_mm', 0),
                'uv_index': current.get('uv', 0),
                'location': location.get('name', self.config["LOCATION_CITY"]),
                'waqi_available': False,
                'weatherapi_available': True
            }
            temp = self.weather_data['temperature']
            condition = self.weather_data['condition']
            self.logger.info(f"WeatherAPI check completed. Temperature: {temp}°C, Condition: {condition}")
            return True
        except Exception as e:
            self.logger.error(f"WeatherAPI check failed: {e}")
            return False

    def _check_weather_hybrid(self) -> bool:
        """Hybrid approach: Use WAQI for basic weather + WeatherAPI for detailed info"""
        try:
            # Get basic weather from WAQI (should already be available from air quality check)
            waqi_weather = {}
            if self.air_quality_data and 'weather' in self.air_quality_data:
                waqi_weather = self.air_quality_data.get('weather', {})

            # Get detailed weather from WeatherAPI
            weatherapi_success = self._check_weather_weatherapi()

            if weatherapi_success and self.weather_data:
                # Merge: Use WeatherAPI as primary, fill gaps with WAQI
                if waqi_weather.get('temperature') and not self.weather_data.get('temperature'):
                    self.weather_data['temperature'] = waqi_weather['temperature']
                
                if waqi_weather.get('humidity') and not self.weather_data.get('humidity'):
                    self.weather_data['humidity'] = waqi_weather['humidity']
                
                if waqi_weather.get('pressure') and not self.weather_data.get('pressure'):
                    self.weather_data['pressure'] = waqi_weather['pressure']

                self.weather_data['source'] = 'hybrid'
                self.weather_data['waqi_available'] = bool(waqi_weather)
                self.weather_data['weatherapi_available'] = True

                self.logger.info(f"Hybrid weather check completed. Temperature: {self.weather_data['temperature']}°C")
                return True

            # If WeatherAPI failed, fall back to WAQI only
            elif waqi_weather.get('temperature'):
                self.logger.warning("WeatherAPI unavailable, using WAQI weather data only")
                return self._check_weather_from_waqi()

            self.logger.warning("No weather data available from hybrid sources")
            return False

        except Exception as e:
            self.logger.error(f"Hybrid weather check failed: {e}")
            return False

    def _check_weather_openweather(self) -> bool:
        """Fallback: Check weather using OpenWeatherMap API"""
        try:
            params = {
                'lat': self.config["LOCATION_LAT"],
                'lon': self.config["LOCATION_LON"],
                'appid': self.config.get("api", {}).get("openweather_api_key", ""),
            }
            data = self._make_api_request(self.config["WEATHER_API_URL"], params)

            if not data or 'main' not in data:
                self.logger.warning("No weather data received from OpenWeatherMap")
                return False

            main_data = data['main']
            weather_info = data['weather'][0] if data.get('weather') else {}

            temperature = main_data.get('temp', 20)
            humidity = main_data.get('humidity', 50)
            feels_like = main_data.get('feels_like', temperature)
            description = weather_info.get('description', 'Unknown')

            self.weather_data = {
                'source': 'openweathermap',
                'last_check': datetime.now(),
                'temperature': temperature,
                'feels_like': feels_like,
                'humidity': humidity,
                'description': description,
                'location': data.get('name', self.config["LOCATION_CITY"]),
                'waqi_available': False,
                'weatherapi_available': False
            }

            self.logger.info(f"OpenWeatherMap weather check completed. Temperature: {temperature}°C")
            return True

        except Exception as e:
            self.logger.error(f"OpenWeatherMap weather check failed: {e}")
            return False

    def _check_air_quality_waqi(self):
        try:
            url = f"https://api.waqi.info/feed/{self.config['LOCATION_CITY']}/?token={self.waqi_api_key}"
            data = self._make_api_request(url)
            if data and 'data' in data:
                self.air_quality_data = {
                    'source': 'waqi',
                    'aqi': data['data'].get('aqi'),
                    'pm25': data['data'].get('iaqi', {}).get('pm25', {}).get('v'),
                    'pm10': data['data'].get('iaqi', {}).get('pm10', {}).get('v'),
                    'o3': data['data'].get('iaqi', {}).get('o3', {}).get('v'),
                    'no2': data['data'].get('iaqi', {}).get('no2', {}).get('v'),
                    'so2': data['data'].get('iaqi', {}).get('so2', {}).get('v'),
                    'co': data['data'].get('iaqi', {}).get('co', {}).get('v'),
                    'last_check': datetime.now(),
                    'weather': {
                        'temperature': data['data'].get('iaqi', {}).get('t', {}).get('v'),
                        'humidity': data['data'].get('iaqi', {}).get('h', {}).get('v'),
                        'pressure': data['data'].get('iaqi', {}).get('p', {}).get('v'),
                    }
                }
                self.last_air_quality_check = time.time()
        except Exception as e:
            raise e

    def _check_air_quality_openweather(self):
        try:
            params = {
                'lat': self.config["LOCATION_LAT"],
                'lon': self.config["LOCATION_LON"],
                'appid': self.config.get("api", {}).get("openweather_api_key", ""),
            }
            data = self._make_api_request(self.air_pollution_api_url, params)
            if data and 'list' in data and data['list']:
                pollution = data['list'][0]
                self.air_quality_data = {
                    'source': 'openweathermap',
                    'aqi': pollution['main']['aqi'],
                    'pm25': pollution['components'].get('pm2_5'),
                    'pm10': pollution['components'].get('pm10'),
                    'o3': pollution['components'].get('o3'),
                    'no2': pollution['components'].get('no2'),
                    'so2': pollution['components'].get('so2'),
                    'co': pollution['components'].get('co'),
                    'last_check': datetime.now(),
                }
                self.last_air_quality_check = time.time()
        except Exception as e:
            raise e

    def _check_weather_from_waqi(self) -> bool:
        try:
            if not self.air_quality_data or 'weather' not in self.air_quality_data:
                return False
            waqi_weather = self.air_quality_data.get('weather', {})
            self.weather_data = {
                'source': 'waqi',
                'last_check': datetime.now(),
                'temperature': waqi_weather.get('temperature'),
                'humidity': waqi_weather.get('humidity'),
                'pressure': waqi_weather.get('pressure'),
                'location': self.config["LOCATION_CITY"],
                'waqi_available': True,
                'weatherapi_available': False
            }
            self.logger.info(f"WAQI weather check completed. Temperature: {self.weather_data['temperature']}°C")
            return True
        except Exception as e:
            self.logger.error(f"WAQI weather check failed: {e}")
            return False

    def set_earthquake_callback(self, callback: Callable):
        self.earthquake_callback = callback

    def set_air_quality_callback(self, callback: Callable):
        self.air_quality_callback = callback

    def set_temperature_callback(self, callback: Callable):
        self.temperature_callback = callback

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Sensor monitoring started")

    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Sensor monitoring stopped")

    def _monitoring_loop(self):
        while self.running:
            try:
                self.check_earthquakes()
                self.check_air_quality()
                self.check_weather()

                time.sleep(60)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)

    def get_status(self) -> Dict:
        """Get comprehensive sensor manager status"""
        # Check API configurations
        api_status = {
            'waqi': bool(self.waqi_api_key),
            'weatherapi': bool(self.weatherapi_key),
            'openweathermap': bool(self.config.get("api", {}).get("openweather_api_key"))
        }
        
        # Get data sources
        air_quality_source = self.air_quality_data.get('source', 'none') if self.air_quality_data else 'none'
        weather_source = self.weather_data.get('source', 'none') if self.weather_data else 'none'
        
        return {
            'monitoring': self.running,
            'api_configured': api_status,
            'api_keys_valid': any(api_status.values()),
            'last_checks': {
                'earthquake': datetime.fromtimestamp(self.last_earthquake_check) if self.last_earthquake_check else None,
                'air_quality': datetime.fromtimestamp(self.last_air_quality_check) if self.last_air_quality_check else None,
                'weather': datetime.fromtimestamp(self.last_weather_check) if self.last_weather_check else None
            },
            'data_available': {
                'earthquake': bool(self.earthquake_data),
                'air_quality': bool(self.air_quality_data),
                'weather': bool(self.weather_data),
            },
            'data_sources': {
                'air_quality': air_quality_source,
                'weather': weather_source,
                'weather_strategy': self.config.get("api", {}).get("weather_data_source", "hybrid")
            },
            'current_data': {
                'aqi': self.air_quality_data.get('aqi') if self.air_quality_data else None,
                'temperature': self.weather_data.get('temperature') if self.weather_data else None,
                'humidity': self.weather_data.get('humidity') if self.weather_data else None,
                'condition': self.weather_data.get('condition') if self.weather_data else None,
            }
        }
