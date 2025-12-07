import yaml, os

def load_config():
    config = {
        "default_color": [255, 255, 255],
        "red_color": [255, 0, 0], "green_color": [0, 255, 0], "blue_color": [0, 0, 255],
        "yellow_color": [255, 255, 0], "magenta_color": [255, 0, 255], "cyan_color": [0, 255, 255],
        "white_color": [255, 255, 255],
        "brightness_settings": {"default_brightness": 50, "min_brightness": 0, "max_brightness": 100},
        "auto_mode_settings": {"auto_color_cycle_interval": 10},
        "earthquake_alert_color": [255, 0, 0]
    }
    for file in ["configs/colors.yml", "configs/hardware_pins.yml", "configs/automation_thresholds.yml"]:
        if os.path.exists(file):
            with open(file) as f:
                config.update(yaml.safe_load(f) or {})
    return config
