import os, sys, signal, time, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from lumina.hardware.lamp import LampController
from lumina.utils.config import load_config

class App:
    def __init__(self):
        self.config = load_config()
        self.lamp = None
        self.web = None
        self.running = False
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
    
    def run(self):
        print("Starting Lumina...")
        self.lamp = LampController(self.config)
        self.lamp.start_automation()
        
        web_path = "src/lumina/web/app.py"
        if os.path.exists(web_path):
            self.web = subprocess.Popen([sys.executable, web_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.running = True
        print("Lumina running. Press Ctrl+C to stop.")
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
