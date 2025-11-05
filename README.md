# Lumina - Smart Lamp with ML-Powered Intelligence

A focused smart home project featuring an intelligent lamp with advanced machine learning capabilities for personalized lighting automation.

## Features

### Core Smart Lamp Functionality
- **RGB Color Control**: Full spectrum color customization
- **Brightness Adjustment**: Precise lighting intensity control
- **On/Off Automation**: Intelligent power management
- **Hardware Integration**: Raspberry Pi GPIO and LED strip support

### Advanced ML-Powered Intelligence
- **Behavioral Pattern Recognition**: Learns user lighting preferences and routines
- **Sequence-Aware Predictions**: Understands action sequences and timing patterns
- **Environmental Context Integration**: Adapts to weather, temperature, and air quality
- **Adaptive Learning**: Continuously improves predictions through feedback
- **Routine Detection**: Identifies morning/evening patterns and weekday/weekend differences
- **Confidence Calibration**: Provides reliable prediction confidence scores

### Key ML Capabilities
- **61+ Feature Engineering**: Comprehensive behavioral analysis
- **Markov Chain Modeling**: Sequence prediction for action patterns
- **Routine Clustering**: Automatic routine identification and learning
- **Performance Monitoring**: Real-time accuracy tracking and improvement
- **85-90% Expected Accuracy**: High-confidence predictions for common scenarios

## Installation

### From Source
```bash
git clone <repository-url>
cd lumina
pip install -r requirements.txt
python setup.py develop
```

### Quick Demo
```bash
python ml_demo.py
```

## Usage

### Basic Operation
```bash
# Start the main application
python main.py

# Run with web interface
python app.py
```

### ML System Demo
```bash
# Test the ML capabilities
python ml_demo.py
```

### Web Dashboard
The application includes a Streamlit-based web interface for:
- Real-time lamp control
- ML system monitoring
- Performance analytics
- Routine visualization

## Architecture

### Modular Design
- **Hardware Layer**: GPIO, LED control, sensor integration
- **ML System**: Advanced pattern recognition and prediction
- **Web Interface**: User-friendly control and monitoring
- **Database**: Persistent storage for patterns and settings

### ML Pipeline
1. **Data Collection**: Rich behavioral logging with environmental context
2. **Feature Engineering**: 61+ features for comprehensive analysis
3. **Model Training**: Sequence-aware prediction models
4. **Adaptive Learning**: Continuous improvement through feedback
5. **Prediction**: High-confidence action recommendations

## Development

### Testing
```bash
# Run the ML demo to validate functionality
python ml_demo.py
```

### Project Structure
```
src/lumina/
├── ml/                 # Machine Learning System
│   ├── core.py        # Main ML interface
│   ├── data/          # Data collection & preprocessing
│   ├── models/        # Prediction models
│   └── learning/      # Adaptive learning
├── hardware/          # Lamp hardware control
├── web/              # Web dashboard
├── database/         # Data persistence
└── config/           # Configuration management
```

## Contributing

This project focuses on core smart lamp functionality with advanced ML intelligence. Contributions should align with the simplified, modular architecture.

## License

MIT License