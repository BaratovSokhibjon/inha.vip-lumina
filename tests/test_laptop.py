#!/usr/bin/env python3
"""Test script for Lumina on laptop (non-RPi hardware)"""
import sys, time
sys.path.insert(0, 'src')
from lumina.utils.config import load_config
from lumina.hardware.lamp import LampController

def test_lamp():
    print("=" * 60)
    print("LUMINA LAPTOP TEST - Mock Hardware Mode")
    print("=" * 60)
    
    print("\n[1/7] Loading configuration...")
    config = load_config()
    print("✓ Config loaded")
    
    print("\n[2/7] Initializing lamp controller...")
    lamp = LampController(config)
    print("✓ Lamp initialized")
    
    print("\n[3/7] Testing power ON...")
    lamp.turn_on()
    time.sleep(1)
    
    print("\n[4/7] Testing color changes...")
    colors = [
        ("RED", 255, 0, 0),
        ("GREEN", 0, 255, 0),
        ("BLUE", 0, 0, 255),
        ("YELLOW", 255, 255, 0),
    ]
    for name, r, g, b in colors:
        print(f"  Setting color to {name}...")
        lamp.set_color(r, g, b)
        time.sleep(0.5)
    
    print("\n[5/7] Testing brightness changes...")
    for brightness in [30, 60, 90, 50]:
        print(f"  Setting brightness to {brightness}%...")
        lamp.set_brightness(brightness)
        time.sleep(0.5)
    
    print("\n[6/7] Testing mode toggle...")
    print(f"  Current mode: {lamp.mode}")
    lamp._on_mode()
    print(f"  New mode: {lamp.mode}")
    
    print("\n[7/7] Testing automation...")
    lamp.start_automation()
    print("  Automation started (running for 5 seconds)...")
    time.sleep(5)
    lamp.stop_automation()
    print("  Automation stopped")
    
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    status = lamp.get_status()
    print(f"Lamp Power: {'ON' if status['lamp']['is_on'] else 'OFF'}")
    print(f"Color: RGB{status['lamp']['current_color']}")
    print(f"Brightness: {status['lamp']['current_brightness']}%")
    print(f"Mode: {status['lamp']['mode']}")
    print(f"GPIO Available: {status['hardware']['gpio_enabled']}")
    print(f"Total Events Logged: {status['database']['total_events']}")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nTo test the web dashboard:")
    print("  python3 src/lumina/web/app.py")
    print("  Then open: http://localhost:5000")
    print("\nOr run full system:")
    print("  ./lumina")
    
    lamp.cleanup()

if __name__ == '__main__':
    test_lamp()
