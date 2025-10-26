"""
ML Manager for Lumina

Simple machine learning for user pattern recognition:
- Learn user ON/OFF timing patterns
- Learn color preferences by time/day
- Predict user behavior after a learning period
- Auto-adjust lamp based on predictions
"""

import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import joblib

from lumina.database.database import DatabaseManager

class MLManager:
    """Simple ML manager for user pattern learning"""

    def __init__(self, db_manager: DatabaseManager, config):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.config = config

        # ML models
        self.power_model = None
        self.color_model = None
        self.scaler = StandardScaler()

        # Model state
        self.learning_start_date = None
        self.is_trained = False
        self.model_accuracy = 0.0

        # Create models directory
        os.makedirs(os.path.dirname(self.config["system"]["ml_model_path"]), exist_ok=True)

        # Load existing models if available
        self._load_models()

        self.logger.info("ML Manager initialized")

    def _prepare_features(self, patterns: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Convert user patterns to ML features"""
        if not patterns:
            return np.array([]), np.array([]), np.array([])

        features = []
        power_labels = []
        color_labels = []

        for pattern in patterns:
            feature = [
                pattern['hour'],
                pattern['day_of_week'],
                pattern.get('brightness', 50)
            ]
            features.append(feature)

            power_label = 1 if pattern['action'] in ['TURN_ON', 'COLOR_CHANGE'] else 0
            power_labels.append(power_label)

            if pattern['color']:
                r, g, b = pattern['color']
                if r > g and r > b:
                    color_class = 0  # Red dominant
                elif g > r and g > b:
                    color_class = 1  # Green dominant
                elif b > r and b > g:
                    color_class = 2  # Blue dominant
                else:
                    color_class = 3  # Mixed/White
            else:
                color_class = 3  # Default

            color_labels.append(color_class)

        return np.array(features), np.array(power_labels), np.array(color_labels)

    def has_enough_data(self) -> bool:
        """Check if we have enough data for training"""
        patterns = self.db.get_user_patterns(self.config["automation_thresholds"]["ml_learning_period_days"])
        return len(patterns) >= 20

    def can_start_prediction(self) -> bool:
        """Check if the learning period is complete"""
        if not self.learning_start_date:
            patterns = self.db.get_user_patterns(30)
            if patterns:
                self.learning_start_date = datetime.fromisoformat(patterns[0]['timestamp'])
            else:
                return False

        learning_complete = datetime.now() - self.learning_start_date >= timedelta(days=self.config["automation_thresholds"]["ml_learning_period_days"])

        return learning_complete and self.has_enough_data()

    def train_models(self) -> bool:
        """Train ML models on user data"""
        try:
            self.logger.info("Starting ML model training...")

            patterns = self.db.get_user_patterns(self.config["automation_thresholds"]["ml_learning_period_days"])

            if len(patterns) < 10:
                self.logger.warning("Not enough data for training")
                return False

            features, power_labels, color_labels = self._prepare_features(patterns)

            if len(features) == 0:
                self.logger.warning("No valid features found")
                return False

            features_scaled = self.scaler.fit_transform(features)

            if len(np.unique(power_labels)) > 1:
                self.power_model = SVC(kernel='rbf', probability=True, random_state=42)
                self.power_model.fit(features_scaled, power_labels)
                self.logger.info("Power model trained successfully")

            if len(np.unique(color_labels)) > 1:
                self.color_model = SVC(kernel='rbf', probability=True, random_state=42)
                self.color_model.fit(features_scaled, color_labels)
                self.logger.info("Color model trained successfully")

            self.model_accuracy = min(0.8, len(patterns) / 100.0)

            self._save_models()

            self.is_trained = True
            self.logger.info(f"ML training completed. Accuracy estimate: {self.model_accuracy:.2f}")
            return True

        except Exception as e:
            self.logger.error(f"ML training failed: {e}")
            return False

    def predict_power_state(self, hour: int = None, day_of_week: int = None) -> Tuple[bool, float]:
        """Predict if lamp should be ON or OFF"""
        if not self.power_model or not self.is_trained:
            return False, 0.0

        try:
            now = datetime.now()
            hour = hour or now.hour
            day_of_week = day_of_week or now.weekday()

            features = np.array([[hour, day_of_week, 50]])
            features_scaled = self.scaler.transform(features)

            prediction = self.power_model.predict(features_scaled)[0]
            probability = self.power_model.predict_proba(features_scaled)[0].max()

            should_be_on = bool(prediction)
            confidence = float(probability)

            return should_be_on, confidence

        except Exception as e:
            self.logger.error(f"Power prediction failed: {e}")
            return False, 0.0

    def predict_color(self, hour: int = None, day_of_week: int = None) -> Tuple[Tuple[int, int, int], float]:
        """Predict preferred color"""
        if not self.color_model or not self.is_trained:
            return tuple(self.config["default_color"]), 0.0

        try:
            now = datetime.now()
            hour = hour or now.hour
            day_of_week = day_of_week or now.weekday()

            features = np.array([[hour, day_of_week, 50]])
            features_scaled = self.scaler.transform(features)

            color_class = self.color_model.predict(features_scaled)[0]
            probability = self.color_model.predict_proba(features_scaled)[0].max()

            color_map = {
                0: tuple(self.config["red_color"]),
                1: tuple(self.config["green_color"]),
                2: tuple(self.config["blue_color"]),
                3: tuple(self.config["white_color"])
            }

            predicted_color = color_map.get(color_class, tuple(self.config["default_color"]))
            confidence = float(probability)

            return predicted_color, confidence

        except Exception as e:
            self.logger.error(f"Color prediction failed: {e}")
            return tuple(self.config["default_color"]), 0.0

    def should_auto_adjust(self) -> Tuple[bool, Dict]:
        """Check if lamp should be auto-adjusted now"""
        if not self.can_start_prediction():
            return False, {}

        power_pred, power_conf = self.predict_power_state()
        color_pred, color_conf = self.predict_color()

        min_confidence = self.config["automation_thresholds"]["ml_prediction_accuracy_threshold"]

        adjustments = {}
        should_adjust = False

        if power_conf > min_confidence:
            adjustments['power'] = {'state': power_pred, 'confidence': power_conf}
            should_adjust = True

        if color_conf > min_confidence:
            adjustments['color'] = {'rgb': color_pred, 'confidence': color_conf}
            should_adjust = True

        return should_adjust, adjustments

    def _save_models(self):
        """Save trained models to file"""
        try:
            model_data = {
                'power_model': self.power_model,
                'color_model': self.color_model,
                'scaler': self.scaler,
                'learning_start_date': self.learning_start_date,
                'is_trained': self.is_trained,
                'model_accuracy': self.model_accuracy
            }

            joblib.dump(model_data, self.config["system"]["ml_model_path"])
            self.logger.info("Models saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save models: {e}")

    def _load_models(self):
        """Load trained models from file"""
        try:
            if os.path.exists(self.config["system"]["ml_model_path"]):
                model_data = joblib.load(self.config["system"]["ml_model_path"])

                self.power_model = model_data.get('power_model')
                self.color_model = model_data.get('color_model')
                self.scaler = model_data.get('scaler', StandardScaler())
                self.learning_start_date = model_data.get('learning_start_date')
                self.is_trained = model_data.get('is_trained', False)
                self.model_accuracy = model_data.get('model_accuracy', 0.0)

                self.logger.info("Models loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")

    def get_status(self) -> Dict:
        """Get ML manager status"""
        return {
            'learning_period_days': self.config["automation_thresholds"]["ml_learning_period_days"],
            'learning_start_date': self.learning_start_date.isoformat() if self.learning_start_date else None,
            'is_trained': self.is_trained,
            'model_accuracy': self.model_accuracy,
            'can_predict': self.can_start_prediction(),
            'has_enough_data': self.has_enough_data(),
            'data_points': len(self.db.get_user_patterns(self.config["automation_thresholds"]["ml_learning_period_days"]))
        }
