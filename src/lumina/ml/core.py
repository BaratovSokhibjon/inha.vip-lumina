"""
Lumina ML System - Advanced User Pattern Recognition

Main interface for the intelligent lamp learning system.
Integrates data collection, feature engineering, prediction models, and adaptive learning.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from .data.collector import EnhancedDataCollector, UserAction
from .data.preprocessor import FeatureEngineer
from .models.predictor import AdaptivePredictor, PredictionResult
from .learning.adaptive import LearningManager


class LuminaMLSystem:
    """Main ML system for intelligent lamp behavior learning"""

    def __init__(self, db_manager):
        self.logger = logging.getLogger(__name__)

        # Core components
        self.data_collector = EnhancedDataCollector(db_manager)
        self.feature_engineer = FeatureEngineer()
        self.predictor = AdaptivePredictor()
        self.learning_manager = LearningManager()

        # System state
        self.is_initialized = False
        self.last_prediction = None

        self.logger.info("Lumina ML system initialized")

    def initialize(self) -> bool:
        """Initialize the ML system with existing data"""
        try:
            # Load existing user patterns
            actions = self.data_collector.get_recent_patterns(hours=168)  # Last week

            if len(actions) >= 10:
                # Train models on existing data
                success = self.predictor.train(actions)
                if success:
                    self.logger.info(f"ML system initialized with {len(actions)} training samples")
                    self.is_initialized = True
                    return True
                else:
                    self.logger.warning("Failed to train models on existing data")
            else:
                self.logger.info("Insufficient data for initialization, will learn from new interactions")

            self.is_initialized = True
            return True

        except Exception as e:
            self.logger.error(f"ML system initialization failed: {e}")
            return False

    def log_user_action(self, action: str, color: Optional[Tuple[int, int, int]] = None,
                       brightness: Optional[int] = None,
                       environmental_data: Optional[Dict] = None) -> UserAction:
        """Log a user action with rich context"""

        # Log action with enhanced data collection
        user_action = self.data_collector.log_user_action(
            action=action,
            color=color,
            brightness=brightness,
            environmental_data=environmental_data
        )

        # Process feedback if we have a previous prediction
        if self.last_prediction:
            self.learning_manager.process_feedback(
                prediction=self.last_prediction,
                actual_action=action,
                actual_color=color,
                actual_brightness=brightness
            )

        # Check if we should retrain models
        if self.learning_manager.should_retrain():
            self._retrain_models()

        return user_action

    def predict_next_action(self, context_time: Optional[datetime] = None) -> PredictionResult:
        """Predict the next most likely user action"""

        if not self.is_initialized:
            return PredictionResult(
                action="TURN_ON",
                confidence=0.5,
                reasoning="ML system not yet initialized"
            )

        # Get recent actions for context
        recent_actions = self.data_collector.get_recent_patterns(hours=24)

        # Make prediction
        prediction = self.predictor.predict(recent_actions, context_time)

        # Store for feedback
        self.last_prediction = prediction

        return prediction

    def get_system_status(self) -> Dict[str, Union[str, int, float, bool]]:
        """Get comprehensive ML system status"""
        return {
            'initialized': self.is_initialized,
            'training_samples': len(self.data_collector.get_recent_patterns(hours=168)),
            'predictor_trained': self.predictor.sequence_predictor.is_trained,
            'routines_learned': len(self.predictor.routine_learner.learned_routines),
            'performance': self.learning_manager.get_recent_performance(),
            'insights': self.learning_manager.get_learning_insights(),
            'last_prediction': self.last_prediction.action if self.last_prediction else None
        }

    def get_user_routines(self) -> Dict:
        """Get learned user routines and patterns"""
        return self.data_collector.get_user_routines()

    def force_retraining(self) -> bool:
        """Force retraining of all models"""
        return self._retrain_models()

    def _retrain_models(self) -> bool:
        """Retrain models with latest data"""
        try:
            # Get recent training data
            training_actions = self.data_collector.get_recent_patterns(hours=168)

            if len(training_actions) < 10:
                self.logger.warning("Insufficient data for retraining")
                return False

            # Retrain predictor
            success = self.predictor.train(training_actions)

            if success:
                self.learning_manager.last_training = datetime.now()
                self.logger.info("ML models retrained successfully")
            else:
                self.logger.error("ML model retraining failed")

            return success

        except Exception as e:
            self.logger.error(f"Retraining failed: {e}")
            return False

    def get_prediction_stats(self) -> Dict:
        """Get prediction performance statistics"""
        return self.predictor.get_performance_stats()

    def get_learning_insights(self) -> Dict:
        """Get insights from the learning process"""
        return self.learning_manager.get_learning_insights()

    def reset_learning(self):
        """Reset all learned patterns (for testing/debugging)"""
        self.predictor = AdaptivePredictor()
        self.learning_manager = LearningManager()
        self.data_collector.recent_actions.clear()
        self.last_prediction = None
        self.is_initialized = False

        self.logger.info("ML system learning reset")

    def export_model_data(self) -> Dict:
        """Export current model state for backup/debugging"""
        return {
            'system_status': self.get_system_status(),
            'user_routines': self.get_user_routines(),
            'prediction_stats': self.get_prediction_stats(),
            'learning_insights': self.get_learning_insights(),
            'export_timestamp': datetime.now().isoformat()
        }