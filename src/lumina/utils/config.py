"""
Configuration loader for Lumina
"""

import os
import yaml
from dotenv import load_dotenv

def load_config():
    """Load configuration from YAML files and .env file"""
    load_dotenv()

    config = {}

    # Load YAML files
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs"))
    for filename in os.listdir(config_dir):
        if filename.endswith(".yml"):
            with open(os.path.join(config_dir, filename), "r") as f:
                config.update(yaml.safe_load(f))

    # Load sensitive data from .env
    config["api"] = {
        "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
    }

    return config
