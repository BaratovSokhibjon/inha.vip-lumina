"""
Adaptive Learning Manager for Lumina ML System

Continuous learning and model improvement:
- Feedback processing and model updates
- Performance monitoring and analytics
- Automatic retraining triggers
- Learning insights and recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from ..models.predictor import PredictionResult


@dataclass
class FeedbackData:
    """Feedback data for learning"""
    prediction: PredictionResult
    actual_action: str
    actual_color: Optional[Tuple[int, int, int]]
    actual_brightness: Optional[int]
    timestamp: datetime


class LearningManager:
    """Manages adaptive learning and continuous improvement"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Learning data
        self.feedback_history: List[FeedbackData] = []
        self.performance_history: List[Dict] = []
        self.last_training = datetime.now()

        # Learning parameters
        self.retraining_threshold = 20  # Retrain after 20 feedback samples
        self.performance_window = 50  # Analyze last 50 predictions
        self.min_accuracy_for_insight = 0.6

        self.logger.info("Learning manager initialized")

    def process_feedback(self, prediction: PredictionResult, actual_action: str,
                        actual_color: Optional[Tuple[int, int, int]] = None,
                        actual_brightness: Optional[int] = None) -> None:
        """Process feedback from user actions"""

        feedback = FeedbackData(
            prediction=prediction,
            actual_action=actual_action,
            actual_color=actual_color,
            actual_brightness=actual_brightness,
            timestamp=datetime.now()
        )

        self.feedback_history.append(feedback)

        # Keep only recent feedback
        if len(self.feedback_history) > 100:
            self.feedback_history = self.feedback_history[-100:]

        # Update performance metrics
        self._update_performance_metrics()

        self.logger.debug(f"Processed feedback: predicted {prediction.action}, actual {actual_action}")

    def should_retrain(self) -> bool:
        """Determine if models should be retrained"""

        # Check feedback volume
        if len(self.feedback_history) < self.retraining_threshold:
            return False

        # Check time since last training
        time_since_training = datetime.now() - self.last_training
        if time_since_training < timedelta(hours=6):  # Don't retrain too frequently
            return False

        # Check if accuracy has dropped
        recent_performance = self.get_recent_performance()
        if recent_performance.get('accuracy', 1.0) < 0.7:  # Retrain if accuracy below 70%
            self.logger.info("Retraining triggered due to low accuracy")
            return True

        # Check for new patterns (significant change in action distribution)
        if self._detect_pattern_changes():
            self.logger.info("Retraining triggered due to pattern changes")
            return True

        return False

    def get_recent_performance(self) -> Dict[str, float]:
        """Get recent performance metrics"""

        if len(self.feedback_history) < 5:
            return {'accuracy': 0.0, 'avg_confidence': 0.0, 'total_samples': 0}

        recent_feedback = self.feedback_history[-self.performance_window:]

        # Calculate accuracy
        correct_predictions = sum(
            1 for f in recent_feedback
            if f.prediction.action == f.actual_action
        )
        accuracy = correct_predictions / len(recent_feedback)

        # Average confidence
        avg_confidence = sum(f.prediction.confidence for f in recent_feedback) / len(recent_feedback)

        return {
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'total_samples': len(recent_feedback),
            'correct_predictions': correct_predictions
        }

    def get_learning_insights(self) -> Dict:
        """Generate insights from learning data"""

        if len(self.feedback_history) < 10:
            return {'status': 'insufficient_data'}

        insights = {
            'performance_trends': self._analyze_performance_trends(),
            'common_mistakes': self._analyze_common_mistakes(),
            'learning_progress': self._analyze_learning_progress(),
            'recommendations': self._generate_recommendations(),
            'data_quality': self._assess_data_quality()
        }

        return insights

    def _update_performance_metrics(self) -> None:
        """Update performance tracking"""

        current_performance = self.get_recent_performance()
        current_performance['timestamp'] = datetime.now()

        self.performance_history.append(current_performance)

        # Keep only recent history
        if len(self.performance_history) > 20:
            self.performance_history = self.performance_history[-20:]

    def _detect_pattern_changes(self) -> bool:
        """Detect significant changes in user patterns"""

        if len(self.feedback_history) < 20:
            return False

        # Compare recent vs older patterns
        recent = self.feedback_history[-10:]
        older = self.feedback_history[-20:-10]

        # Check action distribution changes
        recent_actions = [f.actual_action for f in recent]
        older_actions = [f.actual_action for f in older]

        recent_dist = self._get_action_distribution(recent_actions)
        older_dist = self._get_action_distribution(older_actions)

        # Simple change detection: if distributions differ significantly
        total_diff = 0
        all_actions = set(recent_dist.keys()) | set(older_dist.keys())

        for action in all_actions:
            recent_pct = recent_dist.get(action, 0)
            older_pct = older_dist.get(action, 0)
            total_diff += abs(recent_pct - older_pct)

        return total_diff > 0.3  # Significant change threshold

    def _get_action_distribution(self, actions: List[str]) -> Dict[str, float]:
        """Get action distribution as percentages"""
        if not actions:
            return {}

        total = len(actions)
        distribution = {}

        for action in set(actions):
            distribution[action] = actions.count(action) / total

        return distribution

    def _analyze_performance_trends(self) -> Dict:
        """Analyze performance trends over time"""

        if len(self.performance_history) < 3:
            return {'trend': 'stable', 'improvement': 0.0}

        recent = [p['accuracy'] for p in self.performance_history[-3:]]
        older = [p['accuracy'] for p in self.performance_history[-6:-3]] if len(self.performance_history) >= 6 else recent

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        improvement = recent_avg - older_avg

        if improvement > 0.05:
            trend = 'improving'
        elif improvement < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'improvement': improvement,
            'recent_accuracy': recent_avg,
            'older_accuracy': older_avg
        }

    def _analyze_common_mistakes(self) -> Dict:
        """Analyze common prediction mistakes"""

        mistakes = []
        for feedback in self.feedback_history:
            if feedback.prediction.action != feedback.actual_action:
                mistakes.append({
                    'predicted': feedback.prediction.action,
                    'actual': feedback.actual_action,
                    'confidence': feedback.prediction.confidence,
                    'time': feedback.timestamp.hour
                })

        if not mistakes:
            return {'total_mistakes': 0}

        # Group by prediction type
        mistake_counts = {}
        for mistake in mistakes:
            key = f"{mistake['predicted']} -> {mistake['actual']}"
            mistake_counts[key] = mistake_counts.get(key, 0) + 1

        most_common = max(mistake_counts.items(), key=lambda x: x[1]) if mistake_counts else None

        return {
            'total_mistakes': len(mistakes),
            'most_common_mistake': most_common[0] if most_common else None,
            'mistake_rate': len(mistakes) / len(self.feedback_history),
            'high_confidence_mistakes': len([m for m in mistakes if m['confidence'] > 0.8])
        }

    def _analyze_learning_progress(self) -> Dict:
        """Analyze learning progress over time"""

        if len(self.performance_history) < 5:
            return {'progress': 'insufficient_data'}

        accuracies = [p['accuracy'] for p in self.performance_history]

        # Simple trend analysis
        if accuracies[-1] > accuracies[0] + 0.1:
            progress = 'improving'
        elif accuracies[-1] < accuracies[0] - 0.1:
            progress = 'declining'
        else:
            progress = 'stable'

        return {
            'progress': progress,
            'start_accuracy': accuracies[0],
            'current_accuracy': accuracies[-1],
            'best_accuracy': max(accuracies),
            'total_training_sessions': len(self.performance_history)
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate learning recommendations"""

        recommendations = []
        performance = self.get_recent_performance()

        if performance['accuracy'] < 0.7:
            recommendations.append("Consider collecting more training data for better accuracy")

        if performance['avg_confidence'] < 0.6:
            recommendations.append("Model confidence is low - may need more consistent patterns")

        mistakes = self._analyze_common_mistakes()
        if mistakes.get('high_confidence_mistakes', 0) > 5:
            recommendations.append("High-confidence predictions are often wrong - review model calibration")

        if len(self.feedback_history) < 50:
            recommendations.append("More user interaction data needed for robust learning")

        return recommendations

    def _assess_data_quality(self) -> Dict:
        """Assess quality of training data"""

        if not self.feedback_history:
            return {'quality': 'no_data'}

        # Check for data diversity
        actions = [f.actual_action for f in self.feedback_history]
        unique_actions = len(set(actions))

        # Check for temporal distribution
        hours = [f.timestamp.hour for f in self.feedback_history]
        unique_hours = len(set(hours))

        # Quality score based on diversity and consistency
        diversity_score = min(unique_actions / 5, 1.0)  # Expect at least 5 different actions
        temporal_score = min(unique_hours / 12, 1.0)  # Data from different times

        overall_quality = (diversity_score + temporal_score) / 2

        if overall_quality > 0.8:
            quality = 'excellent'
        elif overall_quality > 0.6:
            quality = 'good'
        elif overall_quality > 0.4:
            quality = 'fair'
        else:
            quality = 'poor'

        return {
            'quality': quality,
            'diversity_score': diversity_score,
            'temporal_score': temporal_score,
            'overall_score': overall_quality,
            'unique_actions': unique_actions,
            'unique_hours': unique_hours
        }