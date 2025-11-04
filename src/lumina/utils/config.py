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

    # Load all .env variables into config
    # This makes all environment variables available as config keys
    for key, value in os.environ.items():
        # Load all uppercase env vars that look like config (not system vars)
        if key.isupper() and not key.startswith(('PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'LC_', 'XDG_', 'DISPLAY', 'TERM', 'VIRTUAL_ENV')):
            config[key] = value

    # Also keep the api section for backward compatibility
    config["api"] = {
        "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
        "waqi_api_key": os.getenv("WAQI_API_KEY"),
        "weatherapi_key": os.getenv("WEATHERAPI_KEY"),
    }

    return config
