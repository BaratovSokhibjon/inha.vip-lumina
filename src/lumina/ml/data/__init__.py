"""
Advanced Feature Engineering for Lumina ML System

Transforms raw user actions into rich feature vectors for machine learning:
- Temporal features (time patterns, sequences)
- Color features (RGB, HSV, temperature)
- Behavioral features (action sequences, trends)
- Environmental correlations
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict

from .collector import UserAction


class FeatureEngineer:
    """Advanced feature engineering for user pattern recognition"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Feature normalization parameters
        self.color_ranges = {'r': (0, 255), 'g': (0, 255), 'b': (0, 255)}
        self.brightness_range = (0, 100)
        self.time_features_count = 12  # Various time-based features

        self.logger.info("Feature engineer initialized")

    def extract_features(self, actions: List[UserAction], context_time: Optional[datetime] = None) -> np.ndarray:
        """
        Extract comprehensive feature vector from user actions

        Args:
            actions: List of user actions to analyze
            context_time: Time to predict for (defaults to now)

        Returns:
            Feature vector as numpy array
        """
        if not actions:
            return np.zeros(self.get_feature_dimension())

        context_time = context_time or datetime.now()

        features = []

        # 1. Temporal features (12 features)
        temporal_features = self._extract_temporal_features(actions, context_time)
        features.extend(temporal_features)

        # 2. Color features (15 features)
        color_features = self._extract_color_features(actions)
        features.extend(color_features)

        # 3. Brightness features (8 features)
        brightness_features = self._extract_brightness_features(actions)
        features.extend(brightness_features)

        # 4. Sequence features (20 features)
        sequence_features = self._extract_sequence_features(actions)
        features.extend(sequence_features)

        # 5. Environmental features (6 features)
        env_features = self._extract_environmental_features(actions)
        features.extend(env_features)

        return np.array(features, dtype=np.float32)

    def get_feature_dimension(self) -> int:
        """Get total number of features"""
        return 12 + 15 + 8 + 20 + 6  # 61 total features

    def _extract_temporal_features(self, actions: List[UserAction], context_time: datetime) -> List[float]:
        """Extract time-based features"""
        features = []

        # Basic time features
        features.append(context_time.hour / 23.0)  # Normalized hour (0-1)
        features.append(context_time.weekday() / 6.0)  # Normalized day (0-1)
        features.append(1.0 if context_time.weekday() >= 5 else 0.0)  # Is weekend
        features.append(context_time.month / 12.0)  # Normalized month

        # Time pattern features
        recent_actions = [a for a in actions if (context_time - a.timestamp).total_seconds() < 86400]  # Last 24h

        # Hourly distribution (24 bins, but we'll use 6 bins for efficiency)
        hour_bins = [0] * 6
        for action in recent_actions:
            bin_idx = action.timestamp.hour // 4  # 4-hour bins
            hour_bins[min(bin_idx, 5)] += 1

        # Normalize by total actions
        total_recent = len(recent_actions)
        if total_recent > 0:
            hour_bins = [count / total_recent for count in hour_bins]

        features.extend(hour_bins)

        # Time since last action (normalized to hours)
        if recent_actions:
            last_action_time = max(a.timestamp for a in recent_actions)
            hours_since_last = (context_time - last_action_time).total_seconds() / 3600
            features.append(min(hours_since_last / 24.0, 1.0))  # Cap at 24 hours
        else:
            features.append(1.0)  # No recent actions

        # Day of week preferences
        dow_counts = [0] * 7
        for action in actions[-50:]:  # Last 50 actions
            dow_counts[action.timestamp.weekday()] += 1

        total_dow = sum(dow_counts)
        if total_dow > 0:
            dow_prefs = [count / total_dow for count in dow_counts]
        else:
            dow_prefs = [1/7] * 7

        features.extend(dow_prefs[:5])  # Use first 5 days to keep feature count reasonable

        return features

    def _extract_color_features(self, actions: List[UserAction]) -> List[float]:
        """Extract color-related features"""
        features = []

        # Get recent colors (last 20 actions with colors)
        recent_colors = []
        for action in actions[-50:]:  # Look back further for color patterns
            if action.color:
                recent_colors.append(action.color)

        if not recent_colors:
            # No color data - return zeros
            return [0.0] * 15

        # RGB statistics
        r_values = [c[0] for c in recent_colors]
        g_values = [c[1] for c in recent_colors]
        b_values = [c[2] for c in recent_colors]

        # Basic RGB stats (6 features)
        for channel in [r_values, g_values, b_values]:
            features.extend([
                np.mean(channel) / 255.0,  # Mean
                np.std(channel) / 255.0,   # Std deviation
            ])

        # Color temperature analysis (3 features)
        warm_count = 0
        cool_count = 0
        neutral_count = 0

        for color in recent_colors:
            temp = self._classify_color_temperature(color)
            if temp == 'warm':
                warm_count += 1
            elif temp == 'cool':
                cool_count += 1
            else:
                neutral_count += 1

        total_colored = len(recent_colors)
        features.extend([
            warm_count / total_colored,
            cool_count / total_colored,
            neutral_count / total_colored
        ])

        # HSV features (3 features) - convert last color to HSV
        if recent_colors:
            last_color = recent_colors[-1]
            hsv = self._rgb_to_hsv(last_color)
            features.extend([
                hsv[0] / 360.0,  # Hue (0-1)
                hsv[1],          # Saturation (0-1)
                hsv[2]           # Value/Brightness (0-1)
            ])
        else:
            features.extend([0.0, 0.0, 0.0])

        # Color diversity (3 features)
        unique_colors = len(set(recent_colors))
        color_entropy = self._calculate_color_entropy(recent_colors)

        features.extend([
            unique_colors / len(recent_colors),  # Color diversity ratio
            color_entropy,                       # Color entropy
            len(recent_colors) / 50.0           # Recent color activity
        ])

        return features

    def _extract_brightness_features(self, actions: List[UserAction]) -> List[float]:
        """Extract brightness-related features"""
        features = []

        # Get recent brightness values
        recent_brightnesses = []
        for action in actions[-30:]:  # Last 30 actions
            if action.brightness is not None:
                recent_brightnesses.append(action.brightness)

        if not recent_brightnesses:
            return [0.5] * 8  # Default neutral values

        # Basic brightness stats (3 features)
        features.extend([
            np.mean(recent_brightnesses) / 100.0,  # Mean brightness
            np.std(recent_brightnesses) / 100.0,   # Brightness variation
            len(recent_brightnesses) / 30.0       # Brightness activity
        ])

        # Brightness trends (3 features)
        if len(recent_brightnesses) >= 3:
            # Calculate trend over last 3 brightness changes
            trend = np.polyfit(range(len(recent_brightnesses)), recent_brightnesses, 1)[0]
            features.append(np.clip(trend / 50.0, -1.0, 1.0))  # Normalized trend

            # Recent brightness changes
            recent_change = recent_brightnesses[-1] - recent_brightnesses[-2]
            features.append(np.clip(recent_change / 50.0, -1.0, 1.0))

            # Brightness volatility (coefficient of variation)
            if np.mean(recent_brightnesses) > 0:
                volatility = np.std(recent_brightnesses) / np.mean(recent_brightnesses)
                features.append(min(volatility, 2.0) / 2.0)  # Cap and normalize
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0, 0.0])

        # Brightness preferences by time (2 features)
        morning_bright = [b for b, a in zip(recent_brightnesses, actions[-30:])
                         if 6 <= a.timestamp.hour <= 12]
        evening_bright = [b for b, a in zip(recent_brightnesses, actions[-30:])
                         if 18 <= a.timestamp.hour <= 23]

        features.append(np.mean(morning_bright) / 100.0 if morning_bright else 0.5)
        features.append(np.mean(evening_bright) / 100.0 if evening_bright else 0.5)

        return features

    def _extract_sequence_features(self, actions: List[UserAction]) -> List[float]:
        """Extract action sequence features"""
        features = []

        if len(actions) < 3:
            return [0.0] * 20

        # Action type frequencies (4 features)
        action_counts = defaultdict(int)
        for action in actions[-50:]:
            action_counts[action.action] += 1

        total_actions = sum(action_counts.values())
        for action_type in ['TURN_ON', 'TURN_OFF', 'COLOR_CHANGE']:
            features.append(action_counts[action_type] / total_actions if total_actions > 0 else 0.0)

        # Action transitions (8 features)
        transitions = defaultdict(int)
        for i in range(len(actions) - 1):
            transition = f"{actions[i].action}->{actions[i+1].action}"
            transitions[transition] += 1

        # Most common transitions
        common_transitions = ['TURN_ON->COLOR_CHANGE', 'COLOR_CHANGE->TURN_OFF',
                            'TURN_ON->TURN_OFF', 'TURN_OFF->TURN_ON']

        for transition in common_transitions:
            features.append(transitions[transition] / len(actions) if len(actions) > 1 else 0.0)

        # Sequence patterns (4 features)
        recent_sequence = [a.action for a in actions[-10:]]
        features.extend([
            1.0 if 'TURN_ON' in recent_sequence else 0.0,      # Recent on action
            1.0 if 'TURN_OFF' in recent_sequence else 0.0,     # Recent off action
            1.0 if recent_sequence.count('COLOR_CHANGE') > 1 else 0.0,  # Multiple color changes
            len(set(recent_sequence)) / len(recent_sequence)   # Action diversity
        ])

        # Time gaps between actions (4 features)
        if len(actions) >= 2:
            gaps = []
            for i in range(1, len(actions)):
                gap = (actions[i].timestamp - actions[i-1].timestamp).total_seconds() / 60  # minutes
                gaps.append(gap)

            if gaps:
                features.extend([
                    np.mean(gaps) / 60.0,    # Mean gap in hours
                    np.std(gaps) / 60.0,     # Gap variation
                    min(gaps) / 60.0,        # Min gap
                    max(gaps) / 60.0         # Max gap
                ])
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        return features

    def _extract_environmental_features(self, actions: List[UserAction]) -> List[float]:
        """Extract environmental correlation features"""
        features = []

        # Get environmental data from recent actions
        env_data = []
        for action in actions[-20:]:
            if 'environmental' in action.context:
                env = action.context['environmental']
                if any(env.get(key) for key in ['temperature', 'humidity', 'aqi']):
                    env_data.append(env)

        if not env_data:
            return [0.5] * 6  # Neutral defaults

        # Temperature features (2 features)
        temps = [e.get('temperature') for e in env_data if e.get('temperature') is not None]
        if temps:
            features.extend([
                (np.mean(temps) + 20) / 60.0,  # Normalized temp (-20°C to 40°C)
                np.std(temps) / 20.0           # Temp variation
            ])
        else:
            features.extend([0.5, 0.0])

        # Air quality features (2 features)
        aqis = [e.get('aqi') for e in env_data if e.get('aqi') is not None]
        if aqis:
            features.extend([
                np.mean(aqis) / 200.0,        # Normalized AQI
                1.0 if np.mean(aqis) > 100 else 0.0  # Poor air quality flag
            ])
        else:
            features.extend([0.0, 0.0])

        # Weather condition features (2 features)
        conditions = [e.get('weather_condition') for e in env_data if e.get('weather_condition')]
        if conditions:
            # Simple weather categorization
            sunny_count = sum(1 for c in conditions if 'sun' in c.lower())
            rainy_count = sum(1 for c in conditions if 'rain' in c.lower())

            total_conditions = len(conditions)
            features.extend([
                sunny_count / total_conditions,  # Sunny weather ratio
                rainy_count / total_conditions   # Rainy weather ratio
            ])
        else:
            features.extend([0.0, 0.0])

        return features

    def _classify_color_temperature(self, color: Tuple[int, int, int]) -> str:
        """Classify color temperature (warm/cool/neutral)"""
        r, g, b = color

        # Simple classification based on RGB ratios
        warmth_ratio = (r + g * 0.7) / (b + 1)  # Red/yellow vs blue

        if warmth_ratio > 2.5:
            return 'warm'
        elif warmth_ratio < 1.5:
            return 'cool'
        else:
            return 'neutral'

    def _rgb_to_hsv(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSV color space"""
        r, g, b = rgb
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Hue
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation
        s = 0 if max_val == 0 else diff / max_val

        # Value
        v = max_val

        return h, s, v

    def _calculate_color_entropy(self, colors: List[Tuple[int, int, int]]) -> float:
        """Calculate color diversity entropy"""
        if len(colors) <= 1:
            return 0.0

        # Simple color binning (8x8x8 color space)
        color_bins = {}
        for color in colors:
            # Quantize to 8 levels per channel
            r_bin = min(int(color[0] / 32), 7)
            g_bin = min(int(color[1] / 32), 7)
            b_bin = min(int(color[2] / 32), 7)

            bin_key = (r_bin, g_bin, b_bin)
            color_bins[bin_key] = color_bins.get(bin_key, 0) + 1

        # Calculate entropy
        total_colors = len(colors)
        entropy = 0.0

        for count in color_bins.values():
            prob = count / total_colors
            entropy -= prob * np.log2(prob)

        # Normalize by max possible entropy (log2 of number of bins)
        max_entropy = np.log2(len(color_bins)) if color_bins else 0
        return entropy / max_entropy if max_entropy > 0 else 0.0