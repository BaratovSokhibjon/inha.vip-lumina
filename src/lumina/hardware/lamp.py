import time, threading
from lumina.hardware.hardware import HardwareController
from lumina.automation.sensors import SensorManager
from lumina.database.database import DatabaseManager

class LampController:
    def __init__(self, config):
        self.config = config
        self.hardware = HardwareController(config)
        self.sensors = SensorManager(config)
        self.db = DatabaseManager(config)
        
        self.is_on = False
        self.current_color = tuple(config["default_color"])
        self.current_brightness = config["brightness_settings"]["default_brightness"]
        self.mode = "MANUAL"
        
        self.color_cycle = [
            tuple(config["red_color"]), tuple(config["green_color"]), tuple(config["blue_color"]),
            tuple(config["yellow_color"]), tuple(config["magenta_color"]), tuple(config["cyan_color"]),
            tuple(config["white_color"])
        ]
        self.current_color_index = 0
        self.running = False
        self.thread = None
        
        self.hardware.set_power_callback(self._on_power)
        self.hardware.set_color_callback(self._on_color)
        self.hardware.set_mode_callback(self._on_mode)
        self.sensors.set_earthquake_callback(self._on_earthquake)
        
        state = self.db.get_state()
        if state:
            self.is_on = state.get("is_on", False)
            self.current_color = tuple(state.get("current_color", config["default_color"]))
            self.current_brightness = state.get("current_brightness", 50)
            self.mode = state.get("mode", "MANUAL")
            self.current_color_index = state.get("current_color_index", 0)
            self.hardware.current_brightness = self.current_brightness
            if self.is_on:
                self.hardware.turn_on_leds(*self.current_color)
    
    def _on_power(self):
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()
    
    def _on_color(self):
        if self.mode == "MANUAL" and self.is_on:
            self.cycle_color()
    
    def _on_mode(self):
        self.mode = "AUTO" if self.mode == "MANUAL" else "MANUAL"
    
    def _on_earthquake(self, earthquakes):
        self.hardware.blink_leds(*self.config["earthquake_alert_color"], times=5, interval=0.3)
        self.hardware.play_alert_sound(2.0)
        for eq in earthquakes:
            self.db.log_environmental_data("earthquake", eq["magnitude"], {"place": eq["place"]})
    
    def turn_on(self, color=None):
        color = color or self.current_color
        self.current_color = color
        self.is_on = True
        self.hardware.turn_on_leds(*color)
        self._save_state()
    
    def turn_off(self):
        self.is_on = False
        self.hardware.turn_off_all_leds()
        self._save_state()
    
    def set_color(self, r, g, b):
        self.current_color = (r, g, b)
        if self.is_on:
            self.hardware.turn_on_leds(r, g, b)
        self._save_state()
    
    def cycle_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.color_cycle)
        self.set_color(*self.color_cycle[self.current_color_index])
    
    def set_brightness(self, brightness):
        self.current_brightness = max(0, min(100, brightness))
        self.hardware.current_brightness = self.current_brightness
        if self.is_on:
            self.hardware.turn_on_leds(*self.current_color)
        self._save_state()
    
    def start_automation(self):
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.hardware.start_button_monitoring()
        self.sensors.start_monitoring()
        self.thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.thread.start()
    
    def stop_automation(self):
        self.running = False
        self.hardware.stop_button_monitoring()
        self.sensors.stop_monitoring()
        if self.thread:
            self.thread.join(timeout=5)
    
    def _automation_loop(self):
        last_brightness = last_cycle = 0
        while self.running:
            try:
                t = time.time()
                if t - last_brightness > 2:
                    brightness = self.hardware.read_potentiometer()
                    if abs(brightness - self.current_brightness) > 3:
                        self.set_brightness(brightness)
                    last_brightness = t
                
                if self.mode == "AUTO" and self.is_on and t - last_cycle > self.config["auto_mode_settings"]["auto_color_cycle_interval"]:
                    self.cycle_color()
                    last_cycle = t
                
                time.sleep(1)
            except:
                time.sleep(5)
    
    def _save_state(self):
        self.db.save_state({
            "is_on": self.is_on, "current_color": self.current_color,
            "current_brightness": self.current_brightness, "mode": self.mode,
            "current_color_index": self.current_color_index
        })
    
    def get_status(self):
        return {
            "lamp": {"is_on": self.is_on, "current_color": self.current_color, "current_brightness": self.current_brightness, "mode": self.mode},
            "hardware": self.hardware.get_status(),
            "sensors": self.sensors.get_status(),
            "database": self.db.get_stats()
        }
    
    def cleanup(self):
        self.stop_automation()
        self._save_state()
        self.hardware.cleanup()
        self.db.close()
