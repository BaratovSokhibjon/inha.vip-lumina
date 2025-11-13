import requests, threading, time

class SensorManager:
    def __init__(self, config):
        self.config = config
        self.weather_data = {}
        self.air_quality_data = {}
        self.earthquake_cb = self.air_quality_cb = self.temperature_cb = None
        self.running = False
        self.thread = None
    
    def set_earthquake_callback(self, cb): self.earthquake_cb = cb
    def set_air_quality_callback(self, cb): self.air_quality_cb = cb
    def set_temperature_callback(self, cb): self.temperature_cb = cb
    
    def start_monitoring(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop_monitoring(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _monitor_loop(self):
        while self.running:
            try:
                self._check_earthquake()
            except: pass
            time.sleep(300)
    
    def _check_earthquake(self):
        try:
            r = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson", timeout=10)
            if r.status_code == 200 and self.earthquake_cb:
                earthquakes = [{"magnitude": f["properties"]["mag"], "place": f["properties"]["place"], "time": f["properties"]["time"]} for f in r.json().get("features", [])]
                if earthquakes:
                    self.earthquake_cb(earthquakes)
        except: pass
    
    def get_status(self): return {"monitoring": self.running}
