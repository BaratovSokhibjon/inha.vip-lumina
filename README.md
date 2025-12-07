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
python3 tests/test_laptop.py          # Run automated tests
python3 src/lumina/web/app.py         # Start web dashboard only
# Open http://localhost:5000
```
**Run test suite:**
```bash
python3 tests/test_laptop.py
```

**Test web dashboard:**
```bash
python3 src/lumina/web/app.py
# Open http://localhost:5000
# Use buttons to control lamp
# Watch console for mock LED output
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

**Flask Web Dashboard**
- Single-page control interface
- Real-time status updates (5s polling)
- Direct lamp control via HTTP endpoints

**Database**
- Events table for logging
- State table for persistence
- Single SQLite file

## License
MIT