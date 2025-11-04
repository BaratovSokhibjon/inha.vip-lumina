#!/usr/bin/env python3
"""
Direct API testing for Lumina integrations
Tests WAQI, WeatherAPI, and USGS directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv
load_dotenv()

import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_waqi_api():
    """Test WAQI API directly"""
    logger.info("Testing WAQI API...")

    waqi_key = os.getenv("WAQI_API_KEY", "")
    waqi_location = os.getenv("WAQI_LOCATION", "seoul")

    if not waqi_key:
        logger.warning("WAQI_API_KEY not set, skipping WAQI test")
        return

    url = f"https://api.waqi.info/feed/{waqi_location}/"
    params = {'token': waqi_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'ok':
            aqi = data['data']['aqi']
            logger.info(f"WAQI test successful: AQI = {aqi}")
        else:
            logger.error(f"WAQI API error: {data}")

    except Exception as e:
        logger.error(f"WAQI test failed: {e}")

def test_weatherapi():
    """Test WeatherAPI.com directly"""
    logger.info("Testing WeatherAPI.com...")

    weather_key = os.getenv("WEATHERAPI_KEY", "")
    lat = os.getenv("LOCATION_LAT", "37.5665")
    lon = os.getenv("LOCATION_LON", "126.9780")

    if not weather_key:
        logger.warning("WEATHERAPI_KEY not set, skipping WeatherAPI test")
        return

    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        'key': weather_key,
        'q': f"{lat},{lon}",
        'aqi': 'yes'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'current' in data:
            temp = data['current']['temp_c']
            condition = data['current']['condition']['text']
            logger.info(f"WeatherAPI test successful: {temp}°C, {condition}")
        else:
            logger.error(f"WeatherAPI error: {data}")

    except Exception as e:
        logger.error(f"WeatherAPI test failed: {e}")

def test_usgs_api():
    """Test USGS Earthquake API directly"""
    logger.info("Testing USGS Earthquake API...")

    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'features' in data:
            count = len(data['features'])
            logger.info(f"USGS test successful: {count} significant earthquakes in the last hour")
        else:
            logger.error("USGS API error: invalid response")

    except Exception as e:
        logger.error(f"USGS test failed: {e}")

def main():
    """Run all API tests"""
    logger.info("Starting direct API integration tests...")

    test_waqi_api()
    test_weatherapi()
    test_usgs_api()

    logger.info("API tests completed")

if __name__ == "__main__":
    main()