try:
    import RPi.GPIO as GPIO
    import board, neopixel
    HAS_GPIO = True
except:
    HAS_GPIO = False

class HardwareController:
    def __init__(self, config):
        self.config = config
        self.current_brightness = config["brightness_settings"]["default_brightness"]
        self.power_cb = self.color_cb = self.mode_cb = None
        self.mock_brightness = 50
        if HAS_GPIO:
            GPIO.setmode(GPIO.BCM)
            self.pixels = neopixel.NeoPixel(board.D18, 30, brightness=0.5)
        else:
            print("[MOCK MODE] Hardware simulation enabled - GPIO not available")
    
    def set_power_callback(self, cb): self.power_cb = cb
    def set_color_callback(self, cb): self.color_cb = cb
    def set_mode_callback(self, cb): self.mode_cb = cb
    
    def turn_on_leds(self, r, g, b):
        if HAS_GPIO:
            brightness = self.current_brightness / 100
            self.pixels.fill((int(r*brightness), int(g*brightness), int(b*brightness)))
        else:
            print(f"[MOCK] LEDs ON: RGB({r},{g},{b}) @ {self.current_brightness}%")
    
    def turn_off_all_leds(self):
        if HAS_GPIO:
            self.pixels.fill((0, 0, 0))
        else:
            print("[MOCK] LEDs OFF")
    
    def blink_leds(self, r, g, b, times=3, interval=0.5):
        if HAS_GPIO:
            import time
            for _ in range(times):
                self.pixels.fill((r, g, b))
                time.sleep(interval)
                self.pixels.fill((0, 0, 0))
                time.sleep(interval)
        else:
            print(f"[MOCK] LEDs BLINK: RGB({r},{g},{b}) x{times}")
    
    def play_alert_sound(self, duration=1.0):
        if not HAS_GPIO:
            print(f"[MOCK] Alert sound: {duration}s")
    
    def read_potentiometer(self):
        if not HAS_GPIO:
            import random
            self.mock_brightness = max(10, min(90, self.mock_brightness + random.randint(-5, 5)))
            return self.mock_brightness
        return self.current_brightness
    
    def start_button_monitoring(self):
        if not HAS_GPIO:
            print("[MOCK] Button monitoring started (use web dashboard to control)")
    
    def stop_button_monitoring(self): pass
    def get_status(self): return {"gpio_enabled": HAS_GPIO}
    def cleanup(self):
        if HAS_GPIO:
            GPIO.cleanup()
