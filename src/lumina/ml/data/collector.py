"""
Enhanced Data Collection for Lumina ML System

Collects rich behavioral data for pattern recognition:
- User actions with full context
- Environmental correlations
- Temporal patterns
- Sequence tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import json

from lumina.database.database import DatabaseManager


@dataclass
class UserAction:
    """Rich user action data structure"""
    timestamp: datetime
    action: str
    color: Optional[Tuple[int, int, int]]
    brightness: Optional[int]
    context: Dict

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'color': self.color,
            'brightness': self.brightness,
            'context': self.context
        }


class EnhancedDataCollector:
    """Enhanced data collection with rich behavioral context"""

    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager

        # Recent action buffer for sequence analysis
        self.recent_actions: List[UserAction] = []
        self.buffer_size = 10

        self.logger.info("Enhanced data collector initialized")

    def log_user_action(
        self,
        action: str,
        color: Optional[Tuple[int, int, int]] = None,
        brightness: Optional[int] = None,
        environmental_data: Optional[Dict] = None
    ) -> UserAction:
        """Log user action with rich context"""

        now = datetime.now()

        # Get recent actions for sequence context
        recent_context = self._get_recent_action_context()

        # Build environmental context
        env_context = environmental_data or {}
        env_context.update({
            'temperature': env_context.get('temperature'),
            'humidity': env_context.get('humidity'),
            'aqi': env_context.get('aqi'),
            'weather_condition': env_context.get('condition')
        })

        # Create rich context
        context = {
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'is_weekend': now.weekday() >= 5,
            'month': now.month,
            'season': self._get_season(now.month),
            'time_since_last_action': self._get_time_since_last_action(now),
            'recent_actions': recent_context,
            'environmental': env_context,
            'brightness_trend': self._calculate_brightness_trend(),
            'color_temperature': self._calculate_color_temperature(color) if color else None
        }

        # Create action object
        user_action = UserAction(
            timestamp=now,
            action=action,
            color=color,
            brightness=brightness,
            context=context
        )

        # Add to recent actions buffer
        self.recent_actions.append(user_action)
        if len(self.recent_actions) > self.buffer_size:
            self.recent_actions.pop(0)

        # Log to database (both legacy and enhanced formats)
        self._log_to_database(user_action)

        self.logger.debug(f"Logged action: {action} at {now}")
        return user_action

    def _get_recent_action_context(self) -> List[Dict]:
        """Get context from recent actions"""
        return [
            {
                'action': action.action,
                'time_ago_minutes': (datetime.now() - action.timestamp).total_seconds() / 60,
                'color': action.color,
                'brightness': action.brightness
            }
            for action in self.recent_actions[-5:]  # Last 5 actions
        ]

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

    def _get_time_since_last_action(self, now: datetime) -> float:
        """Calculate minutes since last action"""
        if not self.recent_actions:
            return 0.0
        last_action = self.recent_actions[-1]
        return (now - last_action.timestamp).total_seconds() / 60

    def _calculate_brightness_trend(self) -> str:
        """Calculate recent brightness trend"""
        if len(self.recent_actions) < 2:
            return 'stable'

        recent_brightnesses = [
            action.brightness for action in self.recent_actions[-3:]
            if action.brightness is not None
        ]

        if len(recent_brightnesses) < 2:
            return 'stable'

        # Simple trend calculation
        if recent_brightnesses[-1] > recent_brightnesses[0] + 10:
            return 'increasing'
        elif recent_brightnesses[-1] < recent_brightnesses[0] - 10:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_color_temperature(self, color: Tuple[int, int, int]) -> str:
        """Calculate color temperature category"""
        if not color:
            return 'unknown'

        r, g, b = color

        # Simple color temperature estimation
        # Warm: more red/yellow, Cool: more blue
        warmth = (r + g * 0.5) / max(b + 1, 1)  # Avoid division by zero

        if warmth > 2.0:
            return 'warm'
        elif warmth < 1.2:
            return 'cool'
        else:
            return 'neutral'

    def _log_to_database(self, action: UserAction):
        """Log action to database (maintains compatibility)"""
        try:
            # Legacy logging for backward compatibility
            # The database method accepts None values despite type hints
            self.db.log_user_action(  # type: ignore
                action.action,
                action.color,  # type: ignore
                action.brightness  # type: ignore
            )

        except Exception as e:
            self.logger.error(f"Failed to log action to database: {e}")

    def get_recent_patterns(self, hours: int = 24) -> List[UserAction]:
        """Get recent user patterns with full context"""
        try:
            # For now, convert legacy data to enhanced format
            legacy_patterns = self.db.get_user_patterns(days=max(1, hours // 24))

            enhanced_patterns = []
            for pattern in legacy_patterns:
                # Reconstruct basic context from legacy data
                timestamp = datetime.fromisoformat(pattern['timestamp'])
                context = {
                    'hour': pattern['hour'],
                    'day_of_week': pattern['day_of_week'],
                    'is_weekend': pattern['day_of_week'] >= 5,
                    'recent_actions': [],
                    'environmental': {},
                    'brightness_trend': 'unknown',
                    'color_temperature': self._calculate_color_temperature(pattern['color'])
                }

                enhanced_patterns.append(UserAction(
                    timestamp=timestamp,
                    action=pattern['action'],
                    color=pattern['color'],
                    brightness=pattern['brightness'],
                    context=context
                ))

            return enhanced_patterns

        except Exception as e:
            self.logger.error(f"Failed to get recent patterns: {e}")
            return []

    def get_user_routines(self) -> Dict:
        """Analyze user routines and patterns"""
        patterns = self.get_recent_patterns(hours=168)  # Last week

        routines = {
            'morning_routine': self._analyze_time_slot_patterns(patterns, 6, 10),
            'evening_routine': self._analyze_time_slot_patterns(patterns, 18, 23),
            'weekday_patterns': self._analyze_day_patterns(patterns, weekdays=True),
            'weekend_patterns': self._analyze_day_patterns(patterns, weekdays=False),
            'color_preferences': self._analyze_color_preferences(patterns),
            'brightness_patterns': self._analyze_brightness_patterns(patterns)
        }

        return routines

    def _analyze_time_slot_patterns(self, patterns: List[UserAction], start_hour: int, end_hour: int) -> Dict:
        """Analyze patterns for specific time slots"""
        slot_patterns = [p for p in patterns if start_hour <= p.context['hour'] <= end_hour]

        if not slot_patterns:
            return {'actions': [], 'avg_brightness': None, 'common_colors': []}

        actions = [p.action for p in slot_patterns]
        brightnesses = [p.brightness for p in slot_patterns if p.brightness]
        colors = [p.color for p in slot_patterns if p.color]

        return {
            'actions': actions,
            'avg_brightness': sum(brightnesses) / len(brightnesses) if brightnesses else None,
            'common_colors': colors[:5],  # Most recent colors
            'pattern_count': len(slot_patterns)
        }

    def _analyze_day_patterns(self, patterns: List[UserAction], weekdays: bool) -> Dict:
        """Analyze weekday vs weekend patterns"""
        day_patterns = [p for p in patterns if p.context['is_weekend'] == (not weekdays)]

        return {
            'total_actions': len(day_patterns),
            'avg_hour': sum(p.context['hour'] for p in day_patterns) / len(day_patterns) if day_patterns else None
        }

    def _analyze_color_preferences(self, patterns: List[UserAction]) -> Dict:
        """Analyze color preferences"""
        colors = [p.color for p in patterns if p.color]
        temperatures = [p.context.get('color_temperature') for p in patterns if p.context.get('color_temperature')]

        temp_counts = {}
        for temp in temperatures:
            temp_counts[temp] = temp_counts.get(temp, 0) + 1

        return {
            'total_colored_actions': len(colors),
            'temperature_preferences': temp_counts,
            'recent_colors': colors[-10:]  # Last 10 colors
        }

    def _analyze_brightness_patterns(self, patterns: List[UserAction]) -> Dict:
        """Analyze brightness usage patterns"""
        brightnesses = [p.brightness for p in patterns if p.brightness]

        if not brightnesses:
            return {'avg_brightness': None, 'brightness_range': []}

        return {
            'avg_brightness': sum(brightnesses) / len(brightnesses),
            'min_brightness': min(brightnesses),
            'max_brightness': max(brightnesses),
            'brightness_trends': [p.context.get('brightness_trend', 'unknown') for p in patterns[-20:]]
        }