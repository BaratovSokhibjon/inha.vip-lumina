import os, sys, time, subprocess

def main():
    # Find project root (where configs/ exists)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        # Start from cli.py location and go up
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # If configs/ not found, we might be in installed mode
        if not os.path.exists(os.path.join(base_path, 'configs')):
            base_path = os.getcwd()
    
    os.chdir(base_path)
    sys.path.insert(0, os.path.join(base_path, 'src'))
    
    from lumina.hardware.lamp import LampController
    from lumina.utils.config import load_config
    
    lamp = None
    web = None
    
    try:
        print("Starting Lumina...")
        config = load_config()
        lamp = LampController(config)
        lamp.start_automation()
        
        web_path = os.path.join(base_path, "src/lumina/web/app.py")
        if os.path.exists(web_path):
            web = subprocess.Popen([sys.executable, web_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Web dashboard: http://localhost:5000")
        
        print("Lumina running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if lamp:
            lamp.cleanup()
        if web:
            web.terminate()

if __name__ == "__main__":
    main()
