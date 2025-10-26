"""
Hardware Controller for Lumina

This module handles all direct interactions with the hardware components,
including LEDs, buttons, and the potentiometer.
"""

import time
import threading
import logging
from typing import Tuple, Callable, Optional

try:
    import RPi.GPIO as GPIO
    import spidev
    import board
    import neopixel
    import pygame
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False
    print("Warning: Running in simulation mode (not on Raspberry Pi)")

class HardwareController:
    """Independent hardware controller for Lumina"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Hardware state
        self.is_initialized = False
        self.lamp_on = False
        self.current_color = tuple(self.config["default_color"])
        self.current_brightness = self.config["brightness_settings"]["default_brightness"]

        # Button callback functions
        self.power_callback = None
        self.color_callback = None
        self.mode_callback = None

        # Threading control
        self.running = False
        self.button_thread = None

        # Initialize hardware if on Raspberry Pi
        if RASPBERRY_PI:
            self._setup_gpio()
            self._setup_spi()
            self._setup_led_strip()
            self._setup_audio()

        self.is_initialized = True
        self.logger.info("Hardware controller initialized")

    def _setup_gpio(self):
        """Setup GPIO pins for LEDs and buttons"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Setup RGB LED pins as outputs
            for i in range(1, 4):
                pins = self.config["hardware_pins"][f"rgb_led_{i}"]
                for pin in pins.values():
                    GPIO.setup(pin, GPIO.OUT)

            # Setup button pins as inputs with pull-up resistors
            for pin in self.config["hardware_pins"]["buttons"].values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Setup speaker pin
            GPIO.setup(self.config["hardware_pins"]["speaker_pin"], GPIO.OUT)

            self.logger.info("GPIO setup completed")

        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")

    def _setup_spi(self):
        """Setup SPI for MCP3008 ADC"""
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Bus 0, Device 0
            self.spi.max_speed_hz = 1350000
            self.logger.info("SPI setup completed")
        except Exception as e:
            self.logger.error(f"SPI setup failed: {e}")
            self.spi = None

    def _setup_led_strip(self):
        """Setup addressable LED strip using board and neopixel"""
        try:
            self.led_strip = neopixel.NeoPixel(
                board.D18,
                self.config["hardware_pins"]["led_strip"]["count"],
                brightness=1.0,
                auto_write=False,
                pixel_order=neopixel.GRB
            )
            self.logger.info("LED strip setup completed")
        except Exception as e:
            self.logger.error(f"LED strip setup failed: {e}")
            self.led_strip = None

    def _setup_audio(self):
        """Setup audio system"""
        try:
            pygame.mixer.init()
            self.logger.info("Audio system setup completed")
        except Exception as e:
            self.logger.error(f"Audio setup failed: {e}")

    def set_rgb_led(self, led_number: int, r: int, g: int, b: int):
        """Set color for specific RGB LED (1, 2, or 3)"""
        if not RASPBERRY_PI:
            self.logger.info(f"SIMULATION: LED {led_number} set to RGB({r}, {g}, {b})")
            return True

        try:
            pins = self.config["hardware_pins"][f"rgb_led_{led_number}"]
            red_pin, green_pin, blue_pin = pins["red"], pins["green"], pins["blue"]

            red_pwm = GPIO.PWM(red_pin, 1000)
            green_pwm = GPIO.PWM(green_pin, 1000)
            blue_pwm = GPIO.PWM(blue_pin, 1000)

            red_pwm.start(0)
            green_pwm.start(0)
            blue_pwm.start(0)

            brightness_factor = self.current_brightness / 100.0
            red_pwm.ChangeDutyCycle((r / 255.0) * 100 * brightness_factor)
            green_pwm.ChangeDutyCycle((g / 255.0) * 100 * brightness_factor)
            blue_pwm.ChangeDutyCycle((b / 255.0) * 100 * brightness_factor)

            self.current_color = (r, g, b)
            return True

        except Exception as e:
            self.logger.error(f"Failed to set RGB LED {led_number}: {e}")
            return False

    def set_all_leds(self, r: int, g: int, b: int):
        """Set color for all RGB LEDs"""
        success = True
        for led_num in [1, 2, 3]:
            if not self.set_rgb_led(led_num, r, g, b):
                success = False
        return success

    def set_led_strip(self, r: int, g: int, b: int):
        """Set color for entire LED strip"""
        if not RASPBERRY_PI or not self.led_strip:
            self.logger.info(f"SIMULATION: LED strip set to RGB({r}, {g}, {b})")
            return True

        try:
            brightness_factor = self.current_brightness / 100.0
            adjusted_r = int(r * brightness_factor)
            adjusted_g = int(g * brightness_factor)
            adjusted_b = int(b * brightness_factor)

            for i in range(len(self.led_strip)):
                self.led_strip[i] = (adjusted_r, adjusted_g, adjusted_b)

            self.led_strip.show()
            return True

        except Exception as e:
            self.logger.error(f"Failed to set LED strip: {e}")
            return False

    def turn_off_all_leds(self):
        """Turn off all LEDs"""
        self.set_all_leds(0, 0, 0)
        self.set_led_strip(0, 0, 0)
        self.lamp_on = False
        self.logger.info("All LEDs turned off")

    def turn_on_leds(self, r: int = None, g: int = None, b: int = None):
        """Turn on LEDs with specified color or current color"""
        if r is None or g is None or b is None:
            r, g, b = self.current_color

        self.set_all_leds(r, g, b)
        self.set_led_strip(r, g, b)
        self.lamp_on = True
        self.logger.info(f"LEDs turned on with color RGB({r}, {g}, {b})")

    def read_potentiometer(self) -> int:
        """Read potentiometer value for brightness control"""
        if not RASPBERRY_PI or not self.spi:
            import random
            return random.randint(0, 100)

        try:
            channel = self.config["hardware_pins"]["mcp3008"]["brightness_channel"]
            adc_value = self.spi.xfer2([1, (8 + channel) << 4, 0])
            data = ((adc_value[1] & 3) << 8) + adc_value[2]

            brightness = int((data / 1023.0) * 100)
            brightness = max(self.config["brightness_settings"]["min_brightness"], min(self.config["brightness_settings"]["max_brightness"], brightness))

            return brightness

        except Exception as e:
            self.logger.error(f"Failed to read potentiometer: {e}")
            return self.current_brightness

    def is_button_pressed(self, button_pin: int) -> bool:
        """Check if a button is currently pressed"""
        if not RASPBERRY_PI:
            return False

        try:
            return GPIO.input(button_pin) == GPIO.LOW
        except Exception as e:
            self.logger.error(f"Failed to read button {button_pin}: {e}")
            return False

    def set_power_callback(self, callback: Callable):
        self.power_callback = callback

    def set_color_callback(self, callback: Callable):
        self.color_callback = callback

    def set_mode_callback(self, callback: Callable):
        self.mode_callback = callback

    def start_button_monitoring(self):
        if self.button_thread and self.button_thread.is_alive():
            return

        self.running = True
        self.button_thread = threading.Thread(target=self._button_monitor_loop)
        self.button_thread.daemon = True
        self.button_thread.start()
        self.logger.info("Button monitoring started")

    def stop_button_monitoring(self):
        self.running = False
        if self.button_thread:
            self.button_thread.join(timeout=1)
        self.logger.info("Button monitoring stopped")

    def _button_monitor_loop(self):
        last_power_press = 0
        last_color_press = 0
        last_mode_press = 0

        power_pin = self.config["hardware_pins"]["buttons"]["power_button_pin"]
        color_pin = self.config["hardware_pins"]["buttons"]["color_button_pin"]
        mode_pin = self.config["hardware_pins"]["buttons"]["mode_button_pin"]
        debounce_time = self.config["hardware_pins"]["button_debounce_time"]

        while self.running:
            try:
                current_time = time.time()

                if self.is_button_pressed(power_pin) and current_time - last_power_press > debounce_time:
                    last_power_press = current_time
                    if self.power_callback:
                        self.power_callback()

                if self.is_button_pressed(color_pin) and current_time - last_color_press > debounce_time:
                    last_color_press = current_time
                    if self.color_callback:
                        self.color_callback()

                if self.is_button_pressed(mode_pin) and current_time - last_mode_press > debounce_time:
                    last_mode_press = current_time
                    if self.mode_callback:
                        self.mode_callback()

                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in button monitoring: {e}")
                time.sleep(1)

    def play_alert_sound(self, duration: float = 1.0):
        if not RASPBERRY_PI:
            self.logger.info(f"SIMULATION: Playing alert sound for {duration}s")
            return

        try:
            frequency = 1000
            sample_rate = 22050
            frames = int(duration * sample_rate)

            arr = []
            for i in range(frames):
                wave = 4096 * (i % (sample_rate // frequency) < (sample_rate // frequency) // 2)
                arr.append([wave, wave])

            sound = pygame.sndarray.make_sound(arr)
            sound.play()
            time.sleep(duration)

        except Exception as e:
            self.logger.error(f"Failed to play alert sound: {e}")

    def blink_leds(self, r: int, g: int, b: int, times: int = 3, interval: float = 0.5):
        original_state = self.lamp_on
        original_color = self.current_color

        for _ in range(times):
            self.turn_on_leds(r, g, b)
            time.sleep(interval)
            self.turn_off_all_leds()
            time.sleep(interval)

        if original_state:
            self.turn_on_leds(*original_color)

    def get_status(self) -> dict:
        return {
            'initialized': self.is_initialized,
            'lamp_on': self.lamp_on,
            'current_color': self.current_color,
            'current_brightness': self.current_brightness,
            'raspberry_pi': RASPBERRY_PI
        }

    def cleanup(self):
        self.stop_button_monitoring()

        if RASPBERRY_PI:
            self.turn_off_all_leds()
            GPIO.cleanup()

            if self.spi:
                self.spi.close()

        self.logger.info("Hardware cleanup completed")
