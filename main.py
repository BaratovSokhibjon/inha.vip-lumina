import os, sys, signal, time, subprocess, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from lumina.hardware.lamp import LampController
from lumina.utils.config import load_config

class App:
    def __init__(self):
        self.config = load_config()
        self.setup_logging()
        self.lamp = None
        self.web = None
        self.running = False
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())

    def setup_logging(self):
        os.makedirs("logs", exist_ok=True)
        log_level = getattr(logging, self.config.get("system", {}).get("log_level", "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.get("system", {}).get("log_file_path", "logs/lumina.log")),
                logging.StreamHandler()
            ]
        )
    
    def run(self):
        logging.info("Starting Lumina...")
        self.lamp = LampController(self.config)
        self.lamp.start_automation()

        web_path = "src/lumina/web/app.py"
        if os.path.exists(web_path):
            self.web = subprocess.Popen([sys.executable, web_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("Web dashboard started")

        self.running = True
        logging.info("Lumina running. Press Ctrl+C to stop.")
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def shutdown(self):
        if not self.running:
            return
        print("\nStopping...")
        self.running = False
        if self.lamp:
            self.lamp.cleanup()
        if self.web:
            self.web.terminate()

if __name__ == "__main__":
    App().run()
