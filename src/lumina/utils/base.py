"""
Utility Functions for Lumina

Helper functions and utilities:
- File operations (JSON, logging)
- Color conversions and calculations
- Time and date helpers
- System monitoring
- General purpose utilities
"""

import os
import json
import logging
import time
import colorsys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import psutil

class Utils:
    """Utility functions for Lumina project"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # File Operations
    def ensure_directory(self, path: str):
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False

    def save_json(self, filepath: str, data: Dict):
        """Save data to JSON file"""
        try:
            self.ensure_directory(os.path.dirname(filepath))

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True

        except Exception as e:
            self.logger.error(f"Failed to save JSON to {filepath}: {e}")
            return False

    def load_json(self, filepath: str) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r') as f:
                return json.load(f)

        except Exception as e:
            self.logger.error(f"Failed to load JSON from {filepath}: {e}")
            return None

    # Color Utilities
    def get_aqi_color(self, aqi_value, config):
        """Get color based on AQI value"""
        if aqi_value <= 50:
            return tuple(config["aqi_good_color"])
        elif aqi_value <= 100:
            return tuple(config["aqi_moderate_color"])
        elif aqi_value <= 150:
            return tuple(config["aqi_unhealthy_color"])
        else:
            return tuple(config["aqi_dangerous_color"])

    def get_temperature_color(self, temperature, config):
        """Get color based on temperature"""
        if temperature < config["automation_thresholds"]["cold_temperature_threshold"]:
            return tuple(config["cold_color"])
        elif temperature > config["automation_thresholds"]["hot_temperature_threshold"]:
            return tuple(config["hot_color"])
        else:
            return tuple(config["warm_color"])

    # System Monitoring
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'temperature': self.get_cpu_temperature(),
                'uptime': time.time() - psutil.boot_time()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}

    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi)"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return temp
        except:
            try:
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
            except:
                pass
        return None