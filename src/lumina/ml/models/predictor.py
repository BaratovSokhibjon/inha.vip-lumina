"""
Adaptive Predictor for Lumina ML System

Sequence-aware prediction models with confidence calibration:
- Markov chain sequence modeling
- Routine clustering and recognition
- Adaptive confidence scoring
- Multi-model ensemble predictions
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import random

from ..data.collector import UserAction
from ..data.preprocessor import FeatureEngineer


@dataclass
class PredictionResult:
    """Prediction result with confidence and reasoning"""
    action: str
    confidence: float
    reasoning: str
    color: Optional[Tuple[int, int, int]] = None
    brightness: Optional[int] = None
    expected_time: Optional[datetime] = None


class SequencePredictor:
    """Markov chain-based sequence predictor"""

    def __init__(self):
        self.transition_matrix: Dict[str, Dict[str, int]] = {}
        self.action_counts: Dict[str, int] = {}
        self.is_trained = False

    def train(self, actions: List[UserAction]) -> bool:
        """Train the sequence predictor"""
        if len(actions) < 2:
            return False

        # Build transition matrix
        for i in range(len(actions) - 1):
            current_action = actions[i].action
            next_action = actions[i + 1].action

            if current_action not in self.transition_matrix:
                self.transition_matrix[current_action] = {}

            if next_action not in self.transition_matrix[current_action]:
                self.transition_matrix[current_action][next_action] = 0

            self.transition_matrix[current_action][next_action] += 1

            # Count action frequencies
            self.action_counts[current_action] = self.action_counts.get(current_action, 0) + 1

        self.action_counts[actions[-1].action] = self.action_counts.get(actions[-1].action, 0) + 1
        self.is_trained = True
        return True

    def predict_next(self, recent_actions: List[str]) -> Tuple[str, float]:
        """Predict next action based on recent sequence"""
        if not self.is_trained or not recent_actions:
            return "TURN_ON", 0.5

        last_action = recent_actions[-1]

        if last_action not in self.transition_matrix:
            # Fallback to most common action
            if self.action_counts:
                most_common = max(self.action_counts, key=self.action_counts.get)
                return most_common, 0.3
            return "TURN_ON", 0.5

        transitions = self.transition_matrix[last_action]
        if not transitions:
            return "TURN_ON", 0.5

        # Find most likely next action
        total_transitions = sum(transitions.values())
        next_action = max(transitions, key=transitions.get)
        probability = transitions[next_action] / total_transitions

        return next_action, min(probability, 0.95)  # Cap at 95% confidence


class RoutineLearner:
    """Learns and recognizes user routines"""

    def __init__(self):
        self.learned_routines: Dict[str, Dict] = {}
        self.routine_patterns: Dict[str, List[Dict]] = {}

    def analyze_routines(self, actions: List[UserAction]) -> Dict[str, Dict]:
        """Analyze user routines from action history"""
        if len(actions) < 5:
            return {}

        # Group actions by time of day
        time_slots = {
            'morning': (6, 10),
            'afternoon': (11, 17),
            'evening': (18, 22),
            'night': (23, 5)
        }

        routines = {}

        for slot_name, (start_hour, end_hour) in time_slots.items():
            slot_actions = [a for a in actions if start_hour <= a.timestamp.hour <= end_hour]

            if len(slot_actions) >= 3:  # Need at least 3 actions for a routine
                routine = self._extract_routine_pattern(slot_actions)
                if routine:
                    routines[slot_name] = routine

        self.learned_routines = routines
        return routines

    def _extract_routine_pattern(self, actions: List[UserAction]) -> Dict:
        """Extract pattern from actions in a time slot"""
        if not actions:
            return {}

        # Analyze action sequence
        action_sequence = [a.action for a in actions]
        most_common_sequence = self._find_common_sequence(action_sequence)

        # Analyze color preferences
        colors = [a.color for a in actions if a.color]
        avg_color = None
        if colors:
            # Simple average of RGB values
            avg_r = sum(c[0] for c in colors) // len(colors)
            avg_g = sum(c[1] for c in colors) // len(colors)
            avg_b = sum(c[2] for c in colors) // len(colors)
            avg_color = (avg_r, avg_g, avg_b)

        # Analyze brightness preferences
        brightnesses = [a.brightness for a in actions if a.brightness]
        avg_brightness = sum(brightnesses) // len(brightnesses) if brightnesses else None

        return {
            'actions': most_common_sequence,
            'avg_color': avg_color,
            'avg_brightness': avg_brightness,
            'frequency': len(actions),
            'confidence': min(len(actions) / 10, 1.0)  # Higher confidence with more data
        }

    def _find_common_sequence(self, actions: List[str]) -> List[str]:
        """Find the most common action sequence"""
        if len(actions) < 2:
            return actions

        # Simple approach: look for repeated patterns
        sequences = []
        for i in range(len(actions) - 1):
            seq = actions[i:i+2]  # Look at pairs
            sequences.append(seq)

        if not sequences:
            return actions[:2] if len(actions) >= 2 else actions

        # Count sequence frequencies
        seq_counts = {}
        for seq in sequences:
            seq_key = tuple(seq)
            seq_counts[seq_key] = seq_counts.get(seq_key, 0) + 1

        # Return most common sequence
        most_common = max(seq_counts, key=seq_counts.get)
        return list(most_common)

    def predict_from_routine(self, current_time: datetime) -> Optional[PredictionResult]:
        """Predict based on learned routines"""
        hour = current_time.hour

        # Find matching routine
        routine_name = None
        if 6 <= hour <= 10:
            routine_name = 'morning'
        elif 11 <= hour <= 17:
            routine_name = 'afternoon'
        elif 18 <= hour <= 22:
            routine_name = 'evening'
        elif hour >= 23 or hour <= 5:
            routine_name = 'night'

        if routine_name in self.learned_routines:
            routine = self.learned_routines[routine_name]

            # Predict first action in routine
            if routine['actions']:
                action = routine['actions'][0]
                confidence = routine.get('confidence', 0.5)

                return PredictionResult(
                    action=action,
                    confidence=confidence,
                    reasoning=f"Based on learned {routine_name} routine",
                    color=routine.get('avg_color'),
                    brightness=routine.get('avg_brightness')
                )

        return None


class AdaptivePredictor:
    """Main adaptive prediction system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Core prediction components
        self.sequence_predictor = SequencePredictor()
        self.routine_learner = RoutineLearner()
        self.feature_engineer = FeatureEngineer()

        # Prediction history for confidence calibration
        self.prediction_history: List[Dict] = []
        self.history_size = 50

        self.logger.info("Adaptive predictor initialized")

    def train(self, actions: List[UserAction]) -> bool:
        """Train all prediction models"""
        try:
            if len(actions) < 3:
                self.logger.warning("Insufficient data for training")
                return False

            # Train sequence predictor
            seq_success = self.sequence_predictor.train(actions)

            # Analyze routines
            self.routine_learner.analyze_routines(actions)

            success = seq_success
            if success:
                self.logger.info(f"Trained on {len(actions)} actions")
            else:
                self.logger.warning("Training failed")

            return success

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    def predict(self, recent_actions: List[UserAction], context_time: Optional[datetime] = None) -> PredictionResult:
        """Make adaptive prediction based on context"""

        current_time = context_time or datetime.now()

        # Extract features for context-aware prediction
        features = self.feature_engineer.extract_features(recent_actions, current_time)

        # Try routine-based prediction first
        routine_prediction = self.routine_learner.predict_from_routine(current_time)
        if routine_prediction and routine_prediction.confidence > 0.6:
            self._record_prediction(routine_prediction, "routine_based")
            return routine_prediction

        # Fall back to sequence prediction
        recent_action_names = [a.action for a in recent_actions[-5:]]  # Last 5 actions
        seq_action, seq_confidence = self.sequence_predictor.predict_next(recent_action_names)

        # Adjust confidence based on features
        adjusted_confidence = self._calibrate_confidence(seq_confidence, features)

        # Generate reasoning
        reasoning = self._generate_reasoning(seq_action, adjusted_confidence, features)

        # Predict color and brightness based on patterns
        color, brightness = self._predict_visual_settings(seq_action, recent_actions)

        result = PredictionResult(
            action=seq_action,
            confidence=adjusted_confidence,
            reasoning=reasoning,
            color=color,
            brightness=brightness
        )

        self._record_prediction(result, "sequence_based")
        return result

    def _calibrate_confidence(self, base_confidence: float, features: Dict) -> float:
        """Calibrate confidence based on contextual features"""

        confidence = base_confidence

        # Boost confidence for routine times
        if features.get('morning_routine_active') or features.get('evening_routine_active'):
            confidence *= 1.2

        # Reduce confidence for high variability
        if features.get('brightness_variability', 0) > 20:
            confidence *= 0.9

        # Boost confidence for consistent patterns
        if features.get('routine_consistency_score', 0) > 0.7:
            confidence *= 1.1

        # Cap confidence between 0.1 and 0.95
        return max(0.1, min(confidence, 0.95))

    def _generate_reasoning(self, action: str, confidence: float, features: Dict) -> str:
        """Generate human-readable reasoning for prediction"""

        reasons = []

        # Time-based reasoning
        hour = features.get('hour', 12)
        if 6 <= hour <= 10:
            reasons.append("morning routine")
        elif 18 <= hour <= 22:
            reasons.append("evening routine")
        elif hour >= 22 or hour <= 5:
            reasons.append("night time")

        # Pattern-based reasoning
        if features.get('sequence_pattern_score', 0) > 0.5:
            reasons.append("recent action patterns")

        if features.get('action_frequency_score', 0) > 2:
            reasons.append("frequent activity")

        # Environmental reasoning
        temp = features.get('temperature_recent', 20)
        if temp > 25:
            reasons.append("warm weather")
        elif temp < 15:
            reasons.append("cool weather")

        reasoning = f"Predicting {action} based on {' and '.join(reasons)}"
        if confidence > 0.8:
            reasoning += " (high confidence)"
        elif confidence < 0.4:
            reasoning += " (low confidence)"

        return reasoning

    def _predict_visual_settings(self, action: str, recent_actions: List[UserAction]) -> Tuple[Optional[Tuple[int, int, int]], Optional[int]]:
        """Predict color and brightness settings"""

        if not recent_actions:
            return None, None

        # For TURN_ON, predict based on time of day
        if action == "TURN_ON":
            current_hour = datetime.now().hour

            if 6 <= current_hour <= 10:  # Morning
                return (255, 220, 180), 75  # Warm light
            elif 18 <= current_hour <= 22:  # Evening
                return (200, 220, 255), 65  # Cool light
            else:  # Day/Night
                return (255, 255, 255), 50  # Neutral

        # For COLOR_CHANGE, use recent color trends
        elif action == "COLOR_CHANGE":
            recent_colors = [a.color for a in recent_actions[-3:] if a.color]
            if recent_colors:
                # Average recent colors
                avg_r = sum(c[0] for c in recent_colors) // len(recent_colors)
                avg_g = sum(c[1] for c in recent_colors) // len(recent_colors)
                avg_b = sum(c[2] for c in recent_colors) // len(recent_colors)
                return (avg_r, avg_g, avg_b), None

        # For BRIGHTNESS_CHANGE, use recent brightness trends
        elif action == "BRIGHTNESS_CHANGE":
            recent_brightnesses = [a.brightness for a in recent_actions[-3:] if a.brightness]
            if recent_brightnesses:
                avg_brightness = sum(recent_brightnesses) // len(recent_brightnesses)
                return None, avg_brightness

        return None, None

    def _record_prediction(self, prediction: PredictionResult, method: str):
        """Record prediction for analysis"""
        record = {
            'timestamp': datetime.now(),
            'action': prediction.action,
            'confidence': prediction.confidence,
            'method': method,
            'color': prediction.color,
            'brightness': prediction.brightness
        }

        self.prediction_history.append(record)
        if len(self.prediction_history) > self.history_size:
            self.prediction_history.pop(0)

    def get_performance_stats(self) -> Dict:
        """Get prediction performance statistics"""
        if not self.prediction_history:
            return {'total_predictions': 0}

        total = len(self.prediction_history)
        high_confidence = len([p for p in self.prediction_history if p['confidence'] > 0.7])

        return {
            'total_predictions': total,
            'high_confidence_predictions': high_confidence,
            'avg_confidence': sum(p['confidence'] for p in self.prediction_history) / total,
            'prediction_methods': list(set(p['method'] for p in self.prediction_history))
        }