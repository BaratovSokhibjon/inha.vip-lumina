"""
Adaptive Learning System for Lumina ML

Implements continuous learning and model improvement:
- Online learning from prediction feedback
- Model performance monitoring
- Adaptive confidence calibration
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ..models.predictor import PredictionResult


class LearningManager:
    """Manages continuous learning and model adaptation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Learning history
        self.feedback_history = []
        self.model_performance = defaultdict(list)
        self.learning_rate = 0.1

        # Adaptation parameters
        self.confidence_threshold = 0.7
        self.min_training_samples = 20
        self.retraining_interval = timedelta(hours=24)

        # Model state
        self.last_training = None
        self.performance_trend = []

        self.logger.info("Learning manager initialized")

    def process_feedback(self, prediction: PredictionResult, actual_action: str,
                        actual_color: Optional[tuple] = None,
                        actual_brightness: Optional[int] = None) -> Dict[str, Any]:
        """Process prediction feedback for learning"""

        # Calculate accuracy
        action_correct = prediction.action == actual_action
        color_correct = (prediction.color == actual_color) if prediction.color and actual_color else True
        brightness_correct = (prediction.brightness == actual_brightness) if prediction.brightness and actual_brightness else True

        overall_correct = action_correct and color_correct and brightness_correct

        # Store feedback
        feedback = {
            'timestamp': datetime.now(),
            'prediction': prediction,
            'actual': {
                'action': actual_action,
                'color': actual_color,
                'brightness': actual_brightness
            },
            'accuracy': {
                'action': action_correct,
                'color': color_correct,
                'brightness': brightness_correct,
                'overall': overall_correct
            },
            'confidence': prediction.confidence
        }

        self.feedback_history.append(feedback)

        # Update performance metrics
        self._update_performance_metrics(feedback)

        # Keep only recent feedback
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-500:]

        self.logger.debug(f"Processed feedback: {'correct' if overall_correct else 'incorrect'} prediction")

        return {
            'correct': overall_correct,
            'confidence_error': abs(prediction.confidence - (1.0 if overall_correct else 0.0)),
            'learning_opportunity': not overall_correct and prediction.confidence > 0.8
        }

    def should_retrain(self) -> bool:
        """Determine if models should be retrained"""
        if not self.last_training:
            return len(self.feedback_history) >= self.min_training_samples

        # Check time since last training
        time_since_training = datetime.now() - self.last_training
        if time_since_training > self.retraining_interval:
            return True

        # Check if performance has degraded
        recent_performance = self.get_recent_performance(window_hours=6)
        if recent_performance['accuracy'] < 0.6:  # Below 60% accuracy
            return True

        # Check if we have enough new data
        recent_feedback = [f for f in self.feedback_history
                          if f['timestamp'] > self.last_training]
        return len(recent_feedback) >= self.min_training_samples

    def get_recent_performance(self, window_hours: int = 24) -> Dict[str, float]:
        """Get performance metrics for recent predictions"""
        cutoff_time = datetime.now() - timedelta(hours=window_hours)

        recent_feedback = [f for f in self.feedback_history if f['timestamp'] > cutoff_time]

        if not recent_feedback:
            return {'accuracy': 0.0, 'avg_confidence': 0.0, 'sample_count': 0}

        correct_predictions = sum(1 for f in recent_feedback if f['accuracy']['overall'])
        avg_confidence = sum(f['confidence'] for f in recent_feedback) / len(recent_feedback)

        return {
            'accuracy': correct_predictions / len(recent_feedback),
            'avg_confidence': avg_confidence,
            'sample_count': len(recent_feedback)
        }

    def get_learning_insights(self) -> Dict[str, Any]:
        """Extract insights from learning data"""
        insights = {
            'performance_trends': self._analyze_performance_trends(),
            'common_mistakes': self._identify_common_mistakes(),
            'confidence_calibration': self._analyze_confidence_calibration(),
            'temporal_patterns': self._analyze_temporal_patterns()
        }

        return insights

    def _update_performance_metrics(self, feedback):
        """Update rolling performance metrics"""
        # Update performance trend
        self.performance_trend.append({
            'timestamp': feedback['timestamp'],
            'accuracy': feedback['accuracy']['overall'],
            'confidence': feedback['confidence']
        })

        # Keep only recent trend data
        if len(self.performance_trend) > 100:
            self.performance_trend = self.performance_trend[-50:]

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.performance_trend) < 10:
            return {'trend': 'insufficient_data', 'improvement': 0.0}

        # Calculate trend over last 20 predictions
        recent = self.performance_trend[-20:]
        older = self.performance_trend[-40:-20] if len(self.performance_trend) >= 40 else recent

        recent_accuracy = sum(p['accuracy'] for p in recent) / len(recent)
        older_accuracy = sum(p['accuracy'] for p in older) / len(older)

        improvement = recent_accuracy - older_accuracy

        if improvement > 0.1:
            trend = 'improving'
        elif improvement < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'improvement': improvement,
            'recent_accuracy': recent_accuracy,
            'overall_accuracy': sum(p['accuracy'] for p in self.performance_trend) / len(self.performance_trend)
        }

    def _identify_common_mistakes(self) -> List[Dict[str, Any]]:
        """Identify patterns in prediction mistakes"""
        mistakes = [f for f in self.feedback_history if not f['accuracy']['overall']]

        if len(mistakes) < 5:
            return []

        # Group mistakes by type
        mistake_patterns = defaultdict(int)

        for mistake in mistakes:
            pred = mistake['prediction']
            actual = mistake['actual']

            # Categorize mistake
            if pred.action != actual['action']:
                mistake_type = f"action_{pred.action}_vs_{actual['action']}"
            elif pred.color != actual.get('color'):
                mistake_type = "color_mismatch"
            elif pred.brightness != actual.get('brightness'):
                mistake_type = "brightness_mismatch"
            else:
                mistake_type = "other"

            mistake_patterns[mistake_type] += 1

        # Return top mistakes
        sorted_mistakes = sorted(mistake_patterns.items(), key=lambda x: x[1], reverse=True)
        return [
            {'type': mistake_type, 'count': count, 'frequency': count / len(mistakes)}
            for mistake_type, count in sorted_mistakes[:5]
        ]

    def _analyze_confidence_calibration(self) -> Dict[str, float]:
        """Analyze how well confidence scores match actual accuracy"""
        if len(self.feedback_history) < 10:
            return {'calibration_error': 0.0}

        # Group by confidence bins
        confidence_bins = defaultdict(list)

        for feedback in self.feedback_history:
            conf_bin = int(feedback['confidence'] * 10) / 10  # Round to nearest 0.1
            confidence_bins[conf_bin].append(feedback['accuracy']['overall'])

        # Calculate calibration error
        calibration_errors = []
        for conf_level, accuracies in confidence_bins.items():
            if len(accuracies) >= 3:  # Need minimum samples
                actual_accuracy = sum(accuracies) / len(accuracies)
                calibration_errors.append(abs(conf_level - actual_accuracy))

        avg_calibration_error = sum(calibration_errors) / len(calibration_errors) if calibration_errors else 0.0

        return {
            'calibration_error': avg_calibration_error,
            'well_calibrated': avg_calibration_error < 0.1
        }

    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns by time of day"""
        hourly_performance = defaultdict(list)

        for feedback in self.feedback_history:
            hour = feedback['timestamp'].hour
            hourly_performance[hour].append(feedback['accuracy']['overall'])

        # Calculate hourly accuracy
        hourly_stats = {}
        for hour, accuracies in hourly_performance.items():
            if len(accuracies) >= 3:
                hourly_stats[hour] = {
                    'accuracy': sum(accuracies) / len(accuracies),
                    'sample_count': len(accuracies)
                }

        # Find best and worst hours
        if hourly_stats:
            best_hour = max(hourly_stats.keys(), key=lambda h: hourly_stats[h]['accuracy'])
            worst_hour = min(hourly_stats.keys(), key=lambda h: hourly_stats[h]['accuracy'])
        else:
            best_hour = worst_hour = None

        return {
            'hourly_performance': hourly_stats,
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'performance_variance': self._calculate_performance_variance(hourly_stats)
        }

    def _calculate_performance_variance(self, hourly_stats: Dict) -> float:
        """Calculate variance in performance across hours"""
        if len(hourly_stats) < 2:
            return 0.0

        accuracies = [stats['accuracy'] for stats in hourly_stats.values()]
        mean_accuracy = sum(accuracies) / len(accuracies)

        variance = sum((acc - mean_accuracy) ** 2 for acc in accuracies) / len(accuracies)
        return variance ** 0.5  # Standard deviation