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
        self.earthquake_data = {}
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

        self.logger.info("Sensor manager initialized")

    def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.config["system"]["api_timeout"]
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

    def check_earthquakes(self) -> bool:
        """Check for significant earthquakes"""
        current_time = time.time()

        if current_time - self.last_earthquake_check < self.config["automation_thresholds"]["earthquake_check_interval"]:
            return False

        self.logger.info("Checking for earthquakes...")

        try:
            data = self._make_api_request(self.config["api"]["earthquake_api_url"])

            if not data or 'features' not in data:
                self.logger.warning("No earthquake data received")
                return False

            significant_earthquakes = []
            for earthquake in data['features']:
                properties = earthquake.get('properties', {})
                magnitude = properties.get('mag', 0)
                place = properties.get('place', 'Unknown')
                time_stamp = properties.get('time', 0)

                if magnitude >= self.config["automation_thresholds"]["earthquake_min_magnitude"]:
                    earthquake_info = {
                        'magnitude': magnitude,
                        'place': place,
                        'time': datetime.fromtimestamp(time_stamp / 1000),
                        'coordinates': earthquake.get('geometry', {}).get('coordinates', [])
                    }
                    significant_earthquakes.append(earthquake_info)

            self.earthquake_data = {
                'last_check': datetime.now(),
                'significant_earthquakes': significant_earthquakes,
                'total_earthquakes': len(data['features'])
            }

            self.last_earthquake_check = current_time

            if significant_earthquakes and self.earthquake_callback:
                self.earthquake_callback(significant_earthquakes)

            self.logger.info(f"Earthquake check completed. Found {len(significant_earthquakes)} significant earthquakes")
            return True

        except Exception as e:
            self.logger.error(f"Earthquake check failed: {e}")
            return False

    def check_air_quality(self) -> bool:
        """Check air quality using OpenWeatherMap API"""
        current_time = time.time()

        if current_time - self.last_air_quality_check < self.config["automation_thresholds"]["air_quality_check_interval"]:
            return False

        if not self.config["api"]["openweather_api_key"]:
            self.logger.warning("OpenWeatherMap API key not configured")
            return False

        self.logger.info("Checking air quality...")

        try:
            params = {
                'lat': self.config["location"]["latitude"],
                'lon': self.config["location"]["longitude"],
                'appid': self.config["api"]["openweather_api_key"]
            }

            data = self._make_api_request(self.config["api"]["openweather_api_url"], params)

            if not data or 'list' not in data:
                self.logger.warning("No air quality data received")
                return False

            current_aqi_data = data['list'][0]
            aqi_value = current_aqi_data.get('main', {}).get('aqi', 1)
            components = current_aqi_data.get('components', {})

            aqi_mapping = {1: 25, 2: 75, 3: 125, 4: 200, 5: 350}
            standard_aqi = aqi_mapping.get(aqi_value, 50)

            self.air_quality_data = {
                'last_check': datetime.now(),
                'aqi': standard_aqi,
                'aqi_level': aqi_value,
                'components': components,
                'location': f"{self.config['location']['latitude']}, {self.config['location']['longitude']}"
            }

            self.last_air_quality_check = current_time

            if standard_aqi >= self.config["automation_thresholds"]["bad_air_threshold"] and self.air_quality_callback:
                self.air_quality_callback(standard_aqi, aqi_value)

            self.logger.info(f"Air quality check completed. AQI: {standard_aqi}")
            return True

        except Exception as e:
            self.logger.error(f"Air quality check failed: {e}")
            return False

    def check_weather(self) -> bool:
        """Check weather and temperature"""
        current_time = time.time()

        if current_time - self.last_weather_check < self.config["automation_thresholds"]["weather_check_interval"]:
            return False

        if not self.config["api"]["openweather_api_key"]:
            self.logger.warning("OpenWeatherMap API key not configured")
            return False

        self.logger.info("Checking weather...")

        try:
            params = {
                'lat': self.config["location"]["latitude"],
                'lon': self.config["location"]["longitude"],
                'appid': self.config["api"]["openweather_api_key"],
                'units': 'metric'
            }

            data = self._make_api_request(self.config["api"]["weather_api_url"], params)

            if not data or 'main' not in data:
                self.logger.warning("No weather data received")
                return False

            main_data = data['main']
            weather_info = data['weather'][0] if data.get('weather') else {}

            temperature = main_data.get('temp', 20)
            humidity = main_data.get('humidity', 50)
            feels_like = main_data.get('feels_like', temperature)
            description = weather_info.get('description', 'Unknown')

            self.weather_data = {
                'last_check': datetime.now(),
                'temperature': temperature,
                'feels_like': feels_like,
                'humidity': humidity,
                'description': description,
                'location': data.get('name', self.config["location"]["city"])
            }

            self.last_weather_check = current_time

            if self.temperature_callback:
                self.temperature_callback(temperature)

            self.logger.info(f"Weather check completed. Temperature: {temperature}°C")
            return True

        except Exception as e:
            self.logger.error(f"Weather check failed: {e}")
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
        return {
            'monitoring': self.running,
            'api_key_configured': bool(self.config["api"]["openweather_api_key"]),
            'last_checks': {
                'earthquake': datetime.fromtimestamp(self.last_earthquake_check) if self.last_earthquake_check else None,
                'air_quality': datetime.fromtimestamp(self.last_air_quality_check) if self.last_air_quality_check else None,
                'weather': datetime.fromtimestamp(self.last_weather_check) if self.last_weather_check else None
            },
            'data_available': {
                'earthquake': bool(self.earthquake_data),
                'air_quality': bool(self.air_quality_data),
                'weather': bool(self.weather_data),
            }
        }
