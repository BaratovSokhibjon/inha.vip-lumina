"""
Lumina Main Application

This is the main entry point for the Lumina system.
Starts all components and manages the application lifecycle.
"""

import os
import sys
import signal
import time
import logging
import subprocess
import threading

from lumina.hardware.lamp import LampController
from lumina.utils.config import load_config
from lumina.utils.logging import setup_logging

class LuminaApp:
    """Main Lumina application"""

    def __init__(self, debug=False, enable_web=True):
        self.config = load_config()
        setup_logging(self.config["system"]["log_level"])
        self.logger = logging.getLogger(__name__)

        self.debug = debug
        self.enable_web = enable_web

        # Core components
        self.lamp_controller = None
        self.web_process = None
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("Lumina Application initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()

    def start_lamp_controller(self):
        """Initialize and start the lamp controller"""
        self.logger.info("Starting lamp controller...")

        try:
            self.lamp_controller = LampController(self.config)
            self.lamp_controller.start_automation()

            self.logger.info("✓ Lamp controller started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start lamp controller: {e}")
            return False

    def start_web_interface(self):
        """Start the Streamlit web interface"""
        if not self.enable_web:
            self.logger.info("Web interface disabled")
            return True

        self.logger.info("Starting web interface...")

        try:
            web_app_path = os.path.join(os.path.dirname(__file__), "..", "web", "app.py")

            if not os.path.exists(web_app_path):
                self.logger.warning(f"Web app not found at {web_app_path}")
                return False

            # Start Streamlit in a subprocess
            cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                web_app_path,
                "--server.port",
                str(self.config["web"]["port"]),
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
                "--logger.level",
                "warning",
            ]

            self.web_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Give it a moment to start
            time.sleep(3)

            if self.web_process.poll() is None:
                self.logger.info(
                    f"✓ Web interface started on port {self.config['web']['port']}"
                )
                self.logger.info(
                    f"  Access at: http://localhost:{self.config['web']['port']}"
                )
                return True
            else:
                self.logger.error("Web interface failed to start")
                return False

        except Exception as e:
            self.logger.error(f"Failed to start web interface: {e}")
            return False

    def run(self):
        """Run the Lumina application"""
        self.logger.info("Starting Lumina Application...")

        # Start lamp controller
        if not self.start_lamp_controller():
            self.logger.error("Failed to start lamp controller!")
            return False

        # Start web interface
        if not self.start_web_interface() and self.enable_web:
            self.logger.warning("Web interface failed to start, continuing without it...")

        # Mark as running
        self.running = True

        self.logger.info("Lumina system started successfully!")

        # Main application loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")

        return True

    def shutdown(self):
        """Shutdown the application gracefully"""
        if not self.running:
            return

        self.logger.info("Shutting down Lumina Application...")
        self.running = False

        # Stop lamp controller
        if self.lamp_controller:
            self.logger.info("Stopping lamp controller...")
            self.lamp_controller.cleanup()

        # Stop web interface
        if self.web_process:
            self.logger.info("Stopping web interface...")
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.web_process.kill()

        self.logger.info("Lumina Application shutdown completed")
