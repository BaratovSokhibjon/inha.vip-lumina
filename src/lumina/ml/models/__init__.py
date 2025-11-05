"""
Sequence-Aware Prediction Models for Lumina ML System

Implements advanced machine learning models for user pattern recognition:
- Sequence prediction using Markov chains and patterns
- Routine clustering for behavior patterns
- Adaptive learning with confidence scoring
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict
import json

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Fallback for basic math
    class np:
        @staticmethod
        def mean(arr): return sum(arr) / len(arr) if arr else 0
        @staticmethod
        def std(arr): return 0  # Simplified
        @staticmethod
        def polyfit(x, y, deg): return [0]  # Simplified

from ..data.collector import UserAction
from ..data.preprocessor import FeatureEngineer


@dataclass
class PredictionResult:
    """Structured prediction result"""
    action: str
    confidence: float
    color: Optional[Tuple[int, int, int]] = None
    brightness: Optional[int] = None
    reasoning: str = ""
    features_used: Optional[List[str]] = None


class SequencePredictor:
    """Sequence-aware action prediction using Markov chains and patterns"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Transition matrices
        self.action_transitions = defaultdict(lambda: defaultdict(int))
        self.color_transitions = defaultdict(lambda: defaultdict(int))
        self.brightness_transitions = defaultdict(lambda: defaultdict(int))

        # Pattern storage
        self.time_patterns = defaultdict(lambda: defaultdict(int))
        self.routine_patterns = []

        # Model state
        self.is_trained = False
        self.training_samples = 0

        self.logger.info("Sequence predictor initialized")

    def train(self, actions: List[UserAction]) -> bool:
        """Train sequence prediction models"""
        try:
            if len(actions) < 5:
                self.logger.warning("Not enough actions for sequence training")
                return False

            # Sort actions by time
            actions = sorted(actions, key=lambda x: x.timestamp)

            # Build transition matrices
            self._build_transition_matrices(actions)

            # Extract time-based patterns
            self._extract_time_patterns(actions)

            # Identify routine patterns
            self._identify_routines(actions)

            self.training_samples = len(actions)
            self.is_trained = True

            self.logger.info(f"Sequence predictor trained on {len(actions)} actions")
            return True

        except Exception as e:
            self.logger.error(f"Sequence training failed: {e}")
            return False

    def predict_next_action(self, recent_actions: List[UserAction],
                          context_time: datetime) -> PredictionResult:
        """Predict the next most likely action"""

        if not self.is_trained or not recent_actions:
            return PredictionResult(
                action="TURN_ON",
                confidence=0.5,
                reasoning="No training data available"
            )

        # Get current state
        current_action = recent_actions[-1].action if recent_actions else "TURN_OFF"
        current_hour = context_time.hour
        current_dow = context_time.weekday()

        # Predict action sequence
        predicted_action = self._predict_action_sequence(current_action, current_hour, current_dow)

        # Predict color if action involves color
        predicted_color = None
        if predicted_action in ['TURN_ON', 'COLOR_CHANGE']:
            predicted_color = self._predict_color(recent_actions)

        # Predict brightness
        predicted_brightness = self._predict_brightness(recent_actions, current_hour)

        # Calculate confidence
        confidence = self._calculate_prediction_confidence(
            predicted_action, predicted_color, predicted_brightness,
            current_hour, current_dow, recent_actions
        )

        return PredictionResult(
            action=predicted_action,
            confidence=confidence,
            color=predicted_color,
            brightness=predicted_brightness,
            reasoning=f"Based on {current_action} at {current_hour}:00 on day {current_dow}"
        )

    def _build_transition_matrices(self, actions: List[UserAction]):
        """Build Markov chain transition matrices"""
        for i in range(len(actions) - 1):
            current = actions[i]
            next_action = actions[i + 1]

            # Action transitions
            self.action_transitions[current.action][next_action.action] += 1

            # Color transitions (simplified)
            if current.color and next_action.color:
                current_temp = self._classify_color_temp(current.color)
                next_temp = self._classify_color_temp(next_action.color)
                self.color_transitions[current_temp][next_temp] += 1

            # Brightness transitions
            if current.brightness is not None and next_action.brightness is not None:
                current_level = self._classify_brightness(current.brightness)
                next_level = self._classify_brightness(next_action.brightness)
                self.brightness_transitions[current_level][next_level] += 1

    def _extract_time_patterns(self, actions: List[UserAction]):
        """Extract time-based usage patterns"""
        for action in actions:
            hour = action.timestamp.hour
            dow = action.timestamp.weekday()
            action_type = action.action

            self.time_patterns[(hour, dow)][action_type] += 1

    def _identify_routines(self, actions: List[UserAction]):
        """Identify common user routines"""
        # Simple routine detection: sequences of actions within short time windows
        routines = []
        current_routine = []
        routine_start = None

        for action in actions:
            if not routine_start:
                routine_start = action.timestamp
                current_routine = [action]
            else:
                time_gap = (action.timestamp - routine_start).total_seconds() / 60  # minutes

                if time_gap < 30:  # 30 minute window
                    current_routine.append(action)
                else:
                    # Save completed routine if meaningful
                    if len(current_routine) >= 3:
                        routines.append(current_routine)

                    # Start new routine
                    routine_start = action.timestamp
                    current_routine = [action]

        # Save final routine
        if len(current_routine) >= 3:
            routines.append(current_routine)

        self.routine_patterns = routines
        self.logger.info(f"Identified {len(routines)} user routines")

    def _predict_action_sequence(self, current_action: str, hour: int, dow: int) -> str:
        """Predict next action based on current state and time"""
        # Get transition probabilities
        transitions = self.action_transitions.get(current_action, {})

        if not transitions:
            # Fallback to time-based patterns
            time_patterns = self.time_patterns.get((hour, dow), {})
            if time_patterns:
                return max(time_patterns.keys(), key=lambda x: time_patterns[x])
            else:
                # Ultimate fallback
                return "TURN_ON" if current_action == "TURN_OFF" else "TURN_OFF"

        # Return most likely next action
        return max(transitions.keys(), key=lambda x: transitions[x])

    def _predict_color(self, recent_actions: List[UserAction]) -> Optional[Tuple[int, int, int]]:
        """Predict next color based on recent actions"""
        if not recent_actions:
            return (255, 255, 255)  # Default white

        # Get recent colors
        recent_colors = [a.color for a in recent_actions[-5:] if a.color]
        if not recent_colors:
            return (255, 255, 255)

        # Simple prediction: return most recent color
        # Could be enhanced with transition matrices
        return recent_colors[-1]

    def _predict_brightness(self, recent_actions: List[UserAction], hour: int) -> Optional[int]:
        """Predict brightness based on time and recent usage"""
        if not recent_actions:
            # Time-based defaults
            if 6 <= hour <= 12:  # Morning
                return 80
            elif 18 <= hour <= 23:  # Evening
                return 60
            else:  # Night
                return 30

        # Get recent brightness values
        recent_brightnesses = [a.brightness for a in recent_actions[-3:] if a.brightness is not None]
        if recent_brightnesses:
            return int(np.mean(recent_brightnesses))

        # Time-based fallback
        return 50

    def _calculate_prediction_confidence(self, action: str, color: Optional[Tuple[int, int, int]],
                                       brightness: Optional[int], hour: int, dow: int,
                                       recent_actions: List[UserAction]) -> float:
        """Calculate confidence score for prediction"""
        confidence = 0.5  # Base confidence

        # Action confidence from transition frequency
        transitions = self.action_transitions.get(recent_actions[-1].action if recent_actions else "TURN_OFF", {})
        total_transitions = sum(transitions.values())
        if total_transitions > 0:
            action_freq = transitions.get(action, 0)
            confidence += (action_freq / total_transitions) * 0.3

        # Time pattern confidence
        time_patterns = self.time_patterns.get((hour, dow), {})
        if time_patterns:
            total_time = sum(time_patterns.values())
            time_freq = time_patterns.get(action, 0)
            confidence += (time_freq / total_time) * 0.2

        # Training data confidence
        if self.training_samples > 0:
            confidence += min(self.training_samples / 100.0, 0.2)  # Up to 0.2 bonus

        return min(confidence, 0.95)

    def _classify_color_temp(self, color: Tuple[int, int, int]) -> str:
        """Classify color temperature"""
        r, g, b = color
        warmth = (r + g * 0.7) / (b + 1)
        if warmth > 2.0:
            return 'warm'
        elif warmth < 1.5:
            return 'cool'
        else:
            return 'neutral'

    def _classify_brightness(self, brightness: int) -> str:
        """Classify brightness level"""
        if brightness < 30:
            return 'low'
        elif brightness < 70:
            return 'medium'
        else:
            return 'high'


class RoutineLearner:
    """Learns and recognizes user routines for proactive automation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Routine storage
        self.learned_routines = []
        self.routine_clusters = defaultdict(list)

        # Routine patterns
        self.morning_routines = []
        self.evening_routines = []
        self.weekend_routines = []

        self.logger.info("Routine learner initialized")

    def learn_routines(self, actions: List[UserAction]) -> bool:
        """Learn user routines from action history"""
        try:
            if len(actions) < 10:
                return False

            # Group actions by time windows
            time_windows = self._group_actions_by_time(actions)

            # Extract routines from time windows
            routines = []
            for window_actions in time_windows:
                if len(window_actions) >= 3:  # Minimum routine length
                    routine = self._extract_routine_pattern(window_actions)
                    if routine:
                        routines.append(routine)

            # Cluster similar routines
            self._cluster_routines(routines)

            # Categorize routines
            self._categorize_routines(routines)

            self.learned_routines = routines
            self.logger.info(f"Learned {len(routines)} user routines")
            return True

        except Exception as e:
            self.logger.error(f"Routine learning failed: {e}")
            return False

    def predict_routine(self, current_time: datetime, recent_actions: List[UserAction]) -> Optional[Dict]:
        """Predict if user is following a known routine"""
        if not self.learned_routines:
            return None

        # Find matching routines for current time/context
        hour = current_time.hour
        dow = current_time.weekday()
        is_weekend = dow >= 5

        candidates = []

        # Check time-based routines
        if 6 <= hour <= 10:  # Morning
            candidates.extend(self.morning_routines)
        elif 18 <= hour <= 23:  # Evening
            candidates.extend(self.evening_routines)

        if is_weekend:
            candidates.extend(self.weekend_routines)

        # Find best matching routine
        best_match = None
        best_score = 0

        for routine in candidates:
            score = self._calculate_routine_match(routine, recent_actions, current_time)
            if score > best_score and score > 0.7:  # 70% match threshold
                best_score = score
                best_match = routine

        if best_match:
            return {
                'routine': best_match,
                'confidence': best_score,
                'next_action': self._predict_next_in_routine(best_match, recent_actions)
            }

        return None

    def _group_actions_by_time(self, actions: List[UserAction]) -> List[List[UserAction]]:
        """Group actions into time-based windows"""
        if not actions:
            return []

        # Sort by time
        actions = sorted(actions, key=lambda x: x.timestamp)

        windows = []
        current_window = [actions[0]]
        window_start = actions[0].timestamp

        for action in actions[1:]:
            time_gap = (action.timestamp - window_start).total_seconds() / 60  # minutes

            if time_gap < 45:  # 45 minute window
                current_window.append(action)
            else:
                # Save current window if meaningful
                if len(current_window) >= 2:
                    windows.append(current_window)

                # Start new window
                current_window = [action]
                window_start = action.timestamp

        # Add final window
        if len(current_window) >= 2:
            windows.append(current_window)

        return windows

    def _extract_routine_pattern(self, window_actions: List[UserAction]) -> Optional[Dict]:
        """Extract a routine pattern from a window of actions"""
        if len(window_actions) < 3:
            return None

        # Calculate time span
        start_time = window_actions[0].timestamp
        end_time = window_actions[-1].timestamp
        duration = (end_time - start_time).total_seconds() / 60  # minutes

        if duration > 60:  # Too long for a routine
            return None

        # Extract action sequence
        action_sequence = [a.action for a in window_actions]

        # Calculate average times (relative to start)
        relative_times = []
        for action in window_actions:
            relative_time = (action.timestamp - start_time).total_seconds() / 60
            relative_times.append(relative_time)

        # Extract color/brightness patterns
        colors = [a.color for a in window_actions if a.color]
        brightnesses = [a.brightness for a in window_actions if a.brightness is not None]

        return {
            'action_sequence': action_sequence,
            'relative_times': relative_times,
            'avg_duration': duration,
            'colors': colors,
            'brightnesses': brightnesses,
            'start_hour': start_time.hour,
            'day_of_week': start_time.weekday(),
            'frequency': 1  # Will be updated during clustering
        }

    def _cluster_routines(self, routines: List[Dict]):
        """Cluster similar routines together"""
        # Simple clustering based on action sequence similarity
        clusters = defaultdict(list)

        for routine in routines:
            # Create signature for clustering
            signature = (
                tuple(routine['action_sequence']),
                routine['start_hour'] // 2,  # 2-hour bins
                routine['day_of_week'] // 2   # Weekday/weekend bins
            )

            clusters[signature].append(routine)

        # Merge similar routines
        merged_routines = []
        for cluster_routines in clusters.values():
            if len(cluster_routines) > 1:
                # Merge cluster into single routine
                merged = self._merge_routine_cluster(cluster_routines)
                merged_routines.append(merged)
            else:
                merged_routines.extend(cluster_routines)

        # Update frequency counts
        for routine in merged_routines:
            signature = (
                tuple(routine['action_sequence']),
                routine['start_hour'] // 2,
                routine['day_of_week'] // 2
            )
            routine['frequency'] = len(clusters[signature])

    def _merge_routine_cluster(self, cluster_routines: List[Dict]) -> Dict:
        """Merge similar routines into one representative routine"""
        # Use the most frequent action sequence
        sequences = [r['action_sequence'] for r in cluster_routines]
        most_common_sequence = max(set(sequences), key=sequences.count)

        # Average times and other properties
        avg_duration = np.mean([r['avg_duration'] for r in cluster_routines])
        avg_start_hour = int(np.mean([r['start_hour'] for r in cluster_routines]))
        avg_dow = int(np.mean([r['day_of_week'] for r in cluster_routines]))

        # Collect all colors/brightnesses
        all_colors = [c for r in cluster_routines for c in r['colors']]
        all_brightnesses = [b for r in cluster_routines for b in r['brightnesses']]

        return {
            'action_sequence': most_common_sequence,
            'relative_times': cluster_routines[0]['relative_times'],  # Use first as template
            'avg_duration': avg_duration,
            'colors': all_colors[-10:],  # Keep recent colors
            'brightnesses': all_brightnesses[-10:],
            'start_hour': avg_start_hour,
            'day_of_week': avg_dow,
            'frequency': len(cluster_routines)
        }

    def _categorize_routines(self, routines: List[Dict]):
        """Categorize routines by time and type"""
        self.morning_routines = [r for r in routines if 6 <= r['start_hour'] <= 10]
        self.evening_routines = [r for r in routines if 18 <= r['start_hour'] <= 23]
        self.weekend_routines = [r for r in routines if r['day_of_week'] >= 5]

    def _calculate_routine_match(self, routine: Dict, recent_actions: List[UserAction],
                               current_time: datetime) -> float:
        """Calculate how well recent actions match a routine"""
        if not recent_actions:
            return 0.0

        # Check time match
        time_diff = abs(current_time.hour - routine['start_hour'])
        time_score = max(0, 1.0 - time_diff / 3.0)  # Within 3 hours

        # Check action sequence match
        recent_sequence = [a.action for a in recent_actions[-len(routine['action_sequence']):]]
        routine_sequence = routine['action_sequence'][:len(recent_sequence)]

        if len(recent_sequence) != len(routine_sequence):
            return 0.0

        # Calculate sequence similarity
        matches = sum(1 for a, b in zip(recent_sequence, routine_sequence) if a == b)
        sequence_score = matches / len(recent_sequence)

        # Combine scores
        return (time_score * 0.4) + (sequence_score * 0.6)

    def _predict_next_in_routine(self, routine: Dict, recent_actions: List[UserAction]) -> Optional[Dict]:
        """Predict the next action in a routine"""
        recent_sequence = [a.action for a in recent_actions[-5:]]
        routine_sequence = routine['action_sequence']

        # Find where we are in the routine
        for i, action in enumerate(routine_sequence):
            if i >= len(recent_sequence):
                break

            if action != recent_sequence[-(i+1)]:
                return None  # Sequence doesn't match

        # Predict next action
        next_idx = len(recent_sequence)
        if next_idx < len(routine_sequence):
            next_action = routine_sequence[next_idx]

            # Get corresponding color/brightness if available
            color = routine['colors'][next_idx] if next_idx < len(routine['colors']) else None
            brightness = routine['brightnesses'][next_idx] if next_idx < len(routine['brightnesses']) else None

            return {
                'action': next_action,
                'color': color,
                'brightness': brightness
            }

        return None


class AdaptivePredictor:
    """Main predictor that combines sequence and routine learning"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Component models
        self.sequence_predictor = SequencePredictor()
        self.routine_learner = RoutineLearner()
        self.feature_engineer = FeatureEngineer()

        # Prediction history for confidence calibration
        self.prediction_history = []

        self.logger.info("Adaptive predictor initialized")

    def train(self, actions: List[UserAction]) -> bool:
        """Train all prediction models"""
        try:
            if len(actions) < 10:
                self.logger.warning("Not enough data for training")
                return False

            # Train sequence predictor
            seq_success = self.sequence_predictor.train(actions)

            # Train routine learner
            routine_success = self.routine_learner.learn_routines(actions)

            success = seq_success or routine_success
            if success:
                self.logger.info("Adaptive predictor training completed")
            else:
                self.logger.warning("Adaptive predictor training failed")

            return success

        except Exception as e:
            self.logger.error(f"Adaptive predictor training failed: {e}")
            return False

    def predict(self, recent_actions: List[UserAction],
               context_time: Optional[datetime] = None) -> PredictionResult:
        """Make comprehensive prediction using all available models"""

        context_time = context_time or datetime.now()

        # Try routine-based prediction first
        routine_prediction = self.routine_learner.predict_routine(context_time, recent_actions)

        if routine_prediction and routine_prediction['confidence'] > 0.8:
            # High confidence routine prediction
            next_action = routine_prediction['next_action']
            if next_action:
                return PredictionResult(
                    action=next_action['action'],
                    confidence=routine_prediction['confidence'],
                    color=next_action.get('color'),
                    brightness=next_action.get('brightness'),
                    reasoning="Routine-based prediction",
                    features_used=['routine_matching', 'sequence_analysis']
                )

        # Fall back to sequence prediction
        sequence_prediction = self.sequence_predictor.predict_next_action(recent_actions, context_time)

        # Enhance with feature-based analysis
        enhanced_prediction = self._enhance_prediction(sequence_prediction, recent_actions, context_time)

        # Calibrate confidence based on history
        calibrated_confidence = self._calibrate_confidence(enhanced_prediction)

        return PredictionResult(
            action=enhanced_prediction.action,
            confidence=calibrated_confidence,
            color=enhanced_prediction.color,
            brightness=enhanced_prediction.brightness,
            reasoning=enhanced_prediction.reasoning,
            features_used=enhanced_prediction.features_used or ['sequence_analysis', 'temporal_patterns']
        )

    def _enhance_prediction(self, base_prediction: PredictionResult,
                          recent_actions: List[UserAction],
                          context_time: datetime) -> PredictionResult:
        """Enhance prediction with additional analysis"""

        # Time-based enhancements
        hour = context_time.hour

        # Morning: prefer warmer colors and higher brightness
        if 6 <= hour <= 10 and base_prediction.action in ['TURN_ON', 'COLOR_CHANGE']:
            if not base_prediction.color:
                base_prediction.color = (255, 200, 150)  # Warm white
            if not base_prediction.brightness:
                base_prediction.brightness = 80

        # Evening: prefer cooler colors and lower brightness
        elif 18 <= hour <= 22 and base_prediction.action in ['TURN_ON', 'COLOR_CHANGE']:
            if not base_prediction.color:
                base_prediction.color = (200, 220, 255)  # Cool white
            if not base_prediction.brightness:
                base_prediction.brightness = 60

        # Night: very low brightness
        elif (22 <= hour or hour <= 5) and base_prediction.action == 'TURN_ON':
            if not base_prediction.brightness:
                base_prediction.brightness = 20

        return base_prediction

    def _calibrate_confidence(self, prediction: PredictionResult) -> float:
        """Calibrate confidence based on prediction history"""
        if not self.prediction_history:
            return prediction.confidence

        # Look at recent prediction accuracy
        recent_predictions = self.prediction_history[-20:]  # Last 20 predictions

        if len(recent_predictions) < 5:
            return prediction.confidence

        # Calculate recent accuracy
        correct_predictions = sum(1 for p in recent_predictions if p.get('was_correct', False))
        recent_accuracy = correct_predictions / len(recent_predictions)

        # Adjust confidence based on recent performance
        if recent_accuracy > 0.8:
            # Good recent performance - slight boost
            return min(prediction.confidence * 1.1, 0.95)
        elif recent_accuracy < 0.5:
            # Poor recent performance - reduce confidence
            return prediction.confidence * 0.8
        else:
            return prediction.confidence

    def record_prediction_result(self, prediction: PredictionResult, actual_action: str,
                               actual_color: Optional[Tuple[int, int, int]] = None,
                               actual_brightness: Optional[int] = None):
        """Record the result of a prediction for learning"""
        was_correct = (
            prediction.action == actual_action and
            (prediction.color == actual_color if prediction.color else True) and
            (prediction.brightness == actual_brightness if prediction.brightness else True)
        )

        result = {
            'timestamp': datetime.now(),
            'predicted_action': prediction.action,
            'actual_action': actual_action,
            'predicted_color': prediction.color,
            'actual_color': actual_color,
            'predicted_brightness': prediction.brightness,
            'actual_brightness': actual_brightness,
            'confidence': prediction.confidence,
            'was_correct': was_correct
        }

        self.prediction_history.append(result)

        # Keep only recent history
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]

    def get_performance_stats(self) -> Dict:
        """Get prediction performance statistics"""
        if not self.prediction_history:
            return {'total_predictions': 0, 'accuracy': 0.0}

        total = len(self.prediction_history)
        correct = sum(1 for p in self.prediction_history if p['was_correct'])

        # Recent accuracy (last 20 predictions)
        recent = self.prediction_history[-20:]
        recent_correct = sum(1 for p in recent if p['was_correct'])
        recent_accuracy = recent_correct / len(recent) if recent else 0.0

        return {
            'total_predictions': total,
            'overall_accuracy': correct / total,
            'recent_accuracy': recent_accuracy,
            'avg_confidence': np.mean([p['confidence'] for p in self.prediction_history])
        }