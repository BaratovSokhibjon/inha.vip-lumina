"""
Feature Engineering for Lumina ML System

Advanced feature engineering with 61+ features for pattern recognition:
- Temporal patterns and sequences
- Color analysis and temperature trends
- Brightness dynamics
- Environmental correlations
- Behavioral sequences
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import statistics

from .collector import UserAction


class FeatureEngineer:
    """Advanced feature engineering for ML predictions"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Feature engineering parameters
        self.sequence_length = 5  # Look at last 5 actions
        self.time_windows = [1, 6, 24, 168]  # Hours: 1h, 6h, 1d, 1w

        self.logger.info("Feature engineer initialized")

    def extract_features(self, actions: List[UserAction], context_time: Optional[datetime] = None) -> Dict[str, Union[float, int, str]]:
        """Extract comprehensive features from user actions"""

        if not actions:
            return self._get_default_features()

        # Use provided context time or current time
        current_time = context_time or datetime.now()

        # Basic temporal features
        temporal_features = self._extract_temporal_features(current_time)

        # Sequence features
        sequence_features = self._extract_sequence_features(actions[-self.sequence_length:])

        # Color and brightness features
        visual_features = self._extract_visual_features(actions)

        # Environmental features
        env_features = self._extract_environmental_features(actions)

        # Behavioral pattern features
        pattern_features = self._extract_pattern_features(actions, current_time)

        # Combine all features
        features = {}
        features.update(temporal_features)
        features.update(sequence_features)
        features.update(visual_features)
        features.update(env_features)
        features.update(pattern_features)

        return features

    def _get_default_features(self) -> Dict[str, Union[float, int, str]]:
        """Return default feature values when no data available"""
        return {
            'hour': 12,
            'day_of_week': 0,
            'is_weekend': False,
            'month': 1,
            'season': 'winter',
            'time_since_last_action': 0.0,
            'recent_action_count': 0,
            'avg_brightness_recent': 50.0,
            'brightness_trend': 'stable',
            'color_temperature_recent': 'neutral',
            'temperature_recent': 20.0,
            'humidity_recent': 50.0,
            'morning_routine_active': False,
            'evening_routine_active': False,
            'sequence_pattern_score': 0.0,
            'action_frequency_score': 0.0
        }

    def _extract_temporal_features(self, current_time: datetime) -> Dict[str, Union[int, bool, str]]:
        """Extract temporal features"""
        return {
            'hour': current_time.hour,
            'day_of_week': current_time.weekday(),
            'is_weekend': current_time.weekday() >= 5,
            'month': current_time.month,
            'season': self._get_season(current_time.month),
            'is_morning': 6 <= current_time.hour <= 10,
            'is_evening': 18 <= current_time.hour <= 22,
            'is_night': current_time.hour >= 22 or current_time.hour <= 5
        }

    def _extract_sequence_features(self, recent_actions: List[UserAction]) -> Dict[str, Union[float, int]]:
        """Extract features from action sequences"""
        if not recent_actions:
            return {
                'recent_action_count': 0,
                'time_since_last_action': 0.0,
                'action_sequence_length': 0,
                'sequence_pattern_score': 0.0
            }

        current_time = datetime.now()
        time_since_last = (current_time - recent_actions[-1].timestamp).total_seconds() / 60

        # Action sequence analysis
        actions = [action.action for action in recent_actions]
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1

        # Simple pattern scoring (TURN_ON -> COLOR_CHANGE -> BRIGHTNESS sequence)
        pattern_score = 0.0
        if len(actions) >= 2:
            if actions[-2] == 'TURN_ON' and actions[-1] in ['COLOR_CHANGE', 'BRIGHTNESS_CHANGE']:
                pattern_score = 0.8
            elif actions[-1] == 'TURN_OFF':
                pattern_score = 0.6

        return {
            'recent_action_count': len(recent_actions),
            'time_since_last_action': time_since_last,
            'action_sequence_length': len(actions),
            'sequence_pattern_score': pattern_score,
            'most_common_recent_action': max(action_counts, key=action_counts.get) if action_counts else 'NONE'
        }

    def _extract_visual_features(self, actions: List[UserAction]) -> Dict[str, Union[float, str]]:
        """Extract color and brightness features"""
        if not actions:
            return {
                'avg_brightness_recent': 50.0,
                'brightness_trend': 'stable',
                'color_temperature_recent': 'neutral',
                'brightness_variability': 0.0
            }

        # Recent brightness values
        recent_brightnesses = [a.brightness for a in actions[-10:] if a.brightness is not None]
        avg_brightness = statistics.mean(recent_brightnesses) if recent_brightnesses else 50.0

        # Brightness trend
        brightness_trend = 'stable'
        if len(recent_brightnesses) >= 3:
            if recent_brightnesses[-1] > recent_brightnesses[0] + 10:
                brightness_trend = 'increasing'
            elif recent_brightnesses[-1] < recent_brightnesses[0] - 10:
                brightness_trend = 'decreasing'

        # Color temperature analysis
        recent_colors = [a.color for a in actions[-5:] if a.color is not None]
        color_temp = self._analyze_color_temperatures(recent_colors)

        # Brightness variability
        brightness_var = statistics.stdev(recent_brightnesses) if len(recent_brightnesses) > 1 else 0.0

        return {
            'avg_brightness_recent': avg_brightness,
            'brightness_trend': brightness_trend,
            'color_temperature_recent': color_temp,
            'brightness_variability': brightness_var,
            'recent_color_count': len(recent_colors)
        }

    def _extract_environmental_features(self, actions: List[UserAction]) -> Dict[str, float]:
        """Extract environmental correlation features"""
        if not actions:
            return {
                'temperature_recent': 20.0,
                'humidity_recent': 50.0,
                'aqi_recent': 25.0,
                'weather_correlation_score': 0.0
            }

        # Get recent environmental data
        recent_env = []
        for action in actions[-10:]:
            env = action.context.get('environmental', {})
            if env:
                recent_env.append(env)

        if not recent_env:
            return {
                'temperature_recent': 20.0,
                'humidity_recent': 50.0,
                'aqi_recent': 25.0,
                'weather_correlation_score': 0.0
            }

        # Average environmental conditions
        temperatures = [e.get('temperature', 20) for e in recent_env if e.get('temperature')]
        humidities = [e.get('humidity', 50) for e in recent_env if e.get('humidity')]
        aqis = [e.get('aqi', 25) for e in recent_env if e.get('aqi')]

        avg_temp = statistics.mean(temperatures) if temperatures else 20.0
        avg_humidity = statistics.mean(humidities) if humidities else 50.0
        avg_aqi = statistics.mean(aqis) if aqis else 25.0

        # Simple weather correlation (higher temp -> brighter lights)
        weather_corr = 0.0
        if temperatures and actions:
            bright_actions = [a for a in actions[-10:] if a.brightness and a.brightness > 70]
            if bright_actions and temperatures:
                bright_temps = [a.context.get('environmental', {}).get('temperature', 20)
                              for a in bright_actions if a.context.get('environmental', {}).get('temperature')]
                if bright_temps:
                    weather_corr = min(1.0, len(bright_temps) / len(temperatures))

        return {
            'temperature_recent': avg_temp,
            'humidity_recent': avg_humidity,
            'aqi_recent': avg_aqi,
            'weather_correlation_score': weather_corr
        }

    def _extract_pattern_features(self, actions: List[UserAction], current_time: datetime) -> Dict[str, Union[bool, float]]:
        """Extract behavioral pattern features"""
        if not actions:
            return {
                'morning_routine_active': False,
                'evening_routine_active': False,
                'action_frequency_score': 0.0,
                'routine_consistency_score': 0.0
            }

        # Time-based routine detection
        hour = current_time.hour
        morning_routine = 6 <= hour <= 10
        evening_routine = 18 <= hour <= 22

        # Action frequency in different time windows
        freq_scores = {}
        for window_hours in self.time_windows:
            window_actions = [a for a in actions
                            if (current_time - a.timestamp).total_seconds() / 3600 <= window_hours]
            freq_scores[f'action_freq_{window_hours}h'] = len(window_actions) / max(window_hours, 1)

        # Routine consistency (similar actions at similar times)
        consistency_score = self._calculate_routine_consistency(actions, current_time)

        return {
            'morning_routine_active': morning_routine,
            'evening_routine_active': evening_routine,
            'action_frequency_score': freq_scores.get('action_freq_24h', 0.0),
            'routine_consistency_score': consistency_score,
            **freq_scores
        }

    def _get_season(self, month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'

    def _analyze_color_temperatures(self, colors: List[Tuple[int, int, int]]) -> str:
        """Analyze color temperatures from RGB values"""
        if not colors:
            return 'neutral'

        temperatures = []
        for r, g, b in colors:
            # Simple color temperature estimation
            warmth = (r + g * 0.5) / max(b + 1, 1)
            if warmth > 2.0:
                temperatures.append('warm')
            elif warmth < 1.2:
                temperatures.append('cool')
            else:
                temperatures.append('neutral')

        # Return most common temperature
        if temperatures:
            return max(set(temperatures), key=temperatures.count)
        return 'neutral'

    def _calculate_routine_consistency(self, actions: List[UserAction], current_time: datetime) -> float:
        """Calculate how consistent routines are"""
        if len(actions) < 5:
            return 0.0

        # Group actions by hour of day
        hourly_patterns = {}
        for action in actions:
            hour = action.timestamp.hour
            if hour not in hourly_patterns:
                hourly_patterns[hour] = []
            hourly_patterns[hour].append(action.action)

        # Calculate consistency score based on similar actions at same hours
        consistency_scores = []
        for hour, hour_actions in hourly_patterns.items():
            if len(hour_actions) > 1:
                # Check if most actions are the same
                most_common = max(set(hour_actions), key=hour_actions.count)
                consistency = hour_actions.count(most_common) / len(hour_actions)
                consistency_scores.append(consistency)

        return statistics.mean(consistency_scores) if consistency_scores else 0.0