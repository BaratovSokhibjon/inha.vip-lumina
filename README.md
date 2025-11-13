# Lumina - Smart Lamp

Ultra-minimal smart lamp with RGB LED control, earthquake alerts, and web dashboard.

## Features
- RGB LED control (NeoPixel strips)
- Hardware buttons and potentiometer
- USGS earthquake monitoring
- Flask web dashboard
- SQLite state persistence

## Installation
```bash
pip install -r requirements.txt
```

## Quick Start

### On Raspberry Pi 4
```bash
./lumina          # Starts lamp automation + web dashboard
```

### On Laptop (Mock Mode)
```bash
python3 test_laptop.py                # Run automated tests
python3 src/lumina/web/app.py         # Start web dashboard only
# Open http://localhost:5000
```

## Testing Without Raspberry Pi

Since GPIO pins aren't available on a laptop, the system automatically enables **Mock Mode**:

**What works in Mock Mode:**
- ✓ Web dashboard (full functionality)
- ✓ Color/brightness changes (printed to console)
- ✓ Mode switching (AUTO/MANUAL)
- ✓ Earthquake monitoring (real USGS API)
- ✓ Database logging
- ✓ State persistence

**Mock output example:**
```
[MOCK MODE] Hardware simulation enabled - GPIO not available
[MOCK] LEDs ON: RGB(255,0,0) @ 80%
[MOCK] LEDs BLINK: RGB(255,0,0) x5
```

**Run test suite:**
```bash
python3 test_laptop.py
```

**Test web dashboard:**
```bash
python3 src/lumina/web/app.py
# Open http://localhost:5000
# Use buttons to control lamp
# Watch console for mock LED output
```

## Project Structure
```
src/lumina/
├── hardware/
│   ├── lamp.py           # Main lamp controller (145 lines)
│   └── hardware.py       # GPIO/LED control (67 lines)
├── automation/
│   └── sensors.py        # Earthquake monitoring (42 lines)
├── database/
│   └── database.py       # SQLite storage (40 lines)
├── utils/
│   └── config.py         # YAML config loader (18 lines)
└── web/
    └── app.py            # Flask dashboard (78 lines)

Total: 407 lines (excluding empty __init__.py files)
```

## Configuration
Edit `configs/` YAML files:
- `hardware_pins.yml` - GPIO pins, button settings
- `colors.yml` - RGB color presets
- `automation_thresholds.yml` - Sensor thresholds

## Architecture

**Hardware Layer**
- Automatic GPIO detection (`HAS_GPIO` flag)
- Graceful fallback to mock mode
- Button callbacks for power/color/mode

**Automation**
- USGS earthquake API monitoring (300s interval)
- Potentiometer brightness control (2s polling)
- AUTO mode color cycling (configurable interval)

**Web Dashboard**
- Single-page control interface
- Real-time status updates (2s polling)
- Direct lamp control via HTTP endpoints

**Database**
- Events table for logging
- State table for persistence
- Single SQLite file

## License
MIT