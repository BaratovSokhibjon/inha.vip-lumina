#!/usr/bin/env python3
"""
Test script for Lumina API integrations
Tests WAQI, WeatherAPI, and USGS earthquake monitoring
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv
load_dotenv()

from lumina.config import settings
from lumina.automation.sensors import SensorManager
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_api_integrations():
    """Test all API integrations"""
    logger.info("Starting API integration tests...")

    # Initialize sensor manager
    sensor_manager = SensorManager(settings)

    # Test air quality (WAQI)
    logger.info("Testing air quality monitoring...")
    try:
        aqi_data = sensor_manager.check_air_quality()
        logger.info(f"Air quality data: {aqi_data}")
    except Exception as e:
        logger.error(f"Air quality test failed: {e}")

    # Test weather
    logger.info("Testing weather monitoring...")
    try:
        weather_data = sensor_manager.check_weather()
        logger.info(f"Weather data: {weather_data}")
    except Exception as e:
        logger.error(f"Weather test failed: {e}")

    # Test earthquake
    logger.info("Testing earthquake monitoring...")
    try:
        eq_data = sensor_manager.check_earthquakes()
        logger.info(f"Earthquake data: {len(eq_data)} events")
    except Exception as e:
        logger.error(f"Earthquake test failed: {e}")

    # Get status
    logger.info("Getting sensor status...")
    try:
        status = sensor_manager.get_status()
        logger.info(f"Sensor status: {status}")
    except Exception as e:
        logger.error(f"Status check failed: {e}")

    logger.info("API integration tests completed")

if __name__ == "__main__":
    test_api_integrations()