#!/usr/bin/env python3
"""
Lumina ML System Demo

Demonstrates the enhanced ML capabilities for user pattern recognition.
Shows how the system learns and predicts user behavior.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lumina.database.database import DatabaseManager
from lumina.ml.core import LuminaMLSystem
from lumina.utils.config import load_config


def simulate_user_patterns(ml_system, db):
    """Simulate realistic user patterns for demonstration"""
    print("🎭 Simulating user behavior patterns...")

    # Simulate morning routine (6-8 AM)
    morning_start = datetime.now().replace(hour=6, minute=0)
    for i in range(10):  # 10 morning sessions
        session_time = morning_start + timedelta(days=i)

        # Morning routine: Turn on -> Warm color -> Adjust brightness
        actions = [
            ("TURN_ON", (255, 200, 150), 60, session_time + timedelta(minutes=0)),
            ("COLOR_CHANGE", (255, 220, 180), 75, session_time + timedelta(minutes=2)),
            ("COLOR_CHANGE", (255, 235, 200), 80, session_time + timedelta(minutes=5)),
            ("TURN_OFF", None, None, session_time + timedelta(hours=2))
        ]

        for action, color, brightness, timestamp in actions:
            # Simulate environmental data
            env_data = {
                'temperature': 18 + (timestamp.hour - 6) * 2,  # Gets warmer
                'humidity': 65,
                'aqi': 25,
                'condition': 'sunny' if timestamp.hour > 7 else 'clear'
            }

            # Log action with environmental context
            ml_system.log_user_action(
                action=action,
                color=color,
                brightness=brightness,
                environmental_data=env_data
            )

    # Simulate evening routine (6-9 PM)
    evening_start = datetime.now().replace(hour=18, minute=0)
    for i in range(8):  # 8 evening sessions
        session_time = evening_start + timedelta(days=i)

        # Evening routine: Turn on -> Cool color -> Reading brightness
        actions = [
            ("TURN_ON", (200, 220, 255), 70, session_time + timedelta(minutes=0)),
            ("COLOR_CHANGE", (180, 200, 255), 65, session_time + timedelta(minutes=3)),
            ("COLOR_CHANGE", (150, 180, 255), 60, session_time + timedelta(minutes=10)),
            ("TURN_OFF", None, None, session_time + timedelta(hours=3))
        ]

        for action, color, brightness, timestamp in actions:
            env_data = {
                'temperature': 22 - (timestamp.hour - 18),  # Cools down
                'humidity': 55,
                'aqi': 35,
                'condition': 'clear'
            }

            ml_system.log_user_action(
                action=action,
                color=color,
                brightness=brightness,
                environmental_data=env_data
            )

    print("✅ Simulated 18 days of user behavior")


def demonstrate_predictions(ml_system):
    """Demonstrate ML prediction capabilities"""
    print("\n🔮 Testing ML Predictions...")

    # Test morning prediction
    morning_time = datetime.now().replace(hour=7, minute=30)
    print(f"\n🌅 Morning prediction (7:30 AM):")
    prediction = ml_system.predict_next_action(morning_time)

    print(f"   Action: {prediction.action}")
    print(f"   Confidence: {prediction.confidence:.1%}")
    if prediction.color:
        print(f"   Color: RGB{prediction.color}")
    if prediction.brightness:
        print(f"   Brightness: {prediction.brightness}%")
    print(f"   Reasoning: {prediction.reasoning}")

    # Test evening prediction
    evening_time = datetime.now().replace(hour=19, minute=15)
    print(f"\n🌙 Evening prediction (7:15 PM):")
    prediction = ml_system.predict_next_action(evening_time)

    print(f"   Action: {prediction.action}")
    print(f"   Confidence: {prediction.confidence:.1%}")
    if prediction.color:
        print(f"   Color: RGB{prediction.color}")
    if prediction.brightness:
        print(f"   Brightness: {prediction.brightness}%")
    print(f"   Reasoning: {prediction.reasoning}")


def show_ml_insights(ml_system):
    """Display ML system insights and analytics"""
    print("\n📊 ML System Insights:")

    # System status
    status = ml_system.get_system_status()
    print(f"   Status: {'Active' if status['initialized'] else 'Learning'}")
    print(f"   Training Samples: {status['training_samples']}")
    print(f"   Routines Learned: {status.get('routines_learned', 'N/A')}")

    # Performance
    perf = status.get('performance', {})
    if perf:
        print(f"   Overall Accuracy: {perf.get('accuracy', 0):.1%}")
        print(f"   Avg Confidence: {perf.get('avg_confidence', 0):.1%}")

    # User routines
    routines = ml_system.get_user_routines()
    if routines:
        print(f"\n🏠 Learned User Routines:")
        morning = routines.get('morning_routine', {})
        if morning.get('actions'):
            print(f"   Morning: {len(morning['actions'])} actions, avg brightness: {morning.get('avg_brightness', 'N/A')}")

        evening = routines.get('evening_routine', {})
        if evening.get('actions'):
            print(f"   Evening: {len(evening['actions'])} actions, avg brightness: {evening.get('avg_brightness', 'N/A')}")

    # Learning insights
    insights = ml_system.get_learning_insights()
    if insights:
        print(f"\n🎯 Learning Insights:")
        trends = insights.get('performance_trends', {})
        if trends.get('trend'):
            print(f"   Performance Trend: {trends['trend']} ({trends.get('improvement', 0):.1%} change)")


def main():
    """Main demo function"""
    print("🧠 Lumina Enhanced ML System Demo")
    print("=" * 50)

    try:
        # Load configuration
        config = load_config()

        # Initialize database and ML system
        db = DatabaseManager(config)
        ml_system = LuminaMLSystem(db)

        # Initialize ML system
        print("🔧 Initializing ML system...")
        ml_system.initialize()

        # Simulate user patterns
        simulate_user_patterns(ml_system, db)

        # Force retraining with new data
        print("🔄 Training ML models on simulated data...")
        ml_system.force_retraining()

        # Demonstrate predictions
        demonstrate_predictions(ml_system)

        # Show insights
        show_ml_insights(ml_system)

        print("\n✅ ML System Demo Complete!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Sequence-aware pattern recognition")
        print("   • Environmental context integration")
        print("   • Routine learning and prediction")
        print("   • Adaptive confidence calibration")
        print("   • Rich behavioral analytics")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()