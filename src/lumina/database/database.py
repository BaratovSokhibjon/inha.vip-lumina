"""
Database Manager for Lumina

This module handles all interactions with the SQLite database.
"""

import sqlite3
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class DatabaseManager:
    """Simple database manager for Lumina"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.db_path = self.config["system"]["database_path"]

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._create_tables()
        self.logger.info(f"Database initialized: {self.db_path}")

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create database tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # User interactions table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        action TEXT NOT NULL,
                        color_r INTEGER,
                        color_g INTEGER,
                        color_b INTEGER,
                        brightness INTEGER,
                        hour INTEGER,
                        day_of_week INTEGER
                    )
                """
                )

                # Environmental data table (enhanced for detailed air quality and weather)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS environmental_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        data_type TEXT NOT NULL,
                        value REAL,
                        details TEXT,
                        source TEXT,
                        location TEXT
                    )
                """
                )

                # System logs table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        level TEXT,
                        message TEXT
                    )
                """
                )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")

    def log_user_action(
        self, action: str, color: Tuple[int, int, int] = None, brightness: int = None
    ):
        """Log user interaction"""
        try:
            now = datetime.now()
            r, g, b = color if color else (None, None, None)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_interactions
                    (action, color_r, color_g, color_b, brightness, hour, day_of_week)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (action, r, g, b, brightness, now.hour, now.weekday()),
                )
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log user action: {e}")

    def log_environmental_data(
        self, data_type: str, value: float, details: Dict = None, source: str = None, location: str = None
    ):
        """Log environmental sensor data"""
        try:
            details_json = json.dumps(details) if details else None

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO environmental_data (data_type, value, details, source, location)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (data_type, value, details_json, source, location),
                )
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log environmental data: {e}")

    def log_air_quality_detailed(self, aqi_data: Dict):
        """Log detailed air quality data from WAQI or other sources"""
        try:
            aqi = aqi_data.get('aqi', 0)
            source = aqi_data.get('source', 'unknown')
            location = aqi_data.get('location', 'Unknown')
            components = aqi_data.get('components', {})
            
            # Log main AQI value
            self.log_environmental_data('aqi', aqi, components, source, location)
            
            self.logger.debug(f"Logged air quality data: AQI={aqi}, Source={source}, Location={location}")

        except Exception as e:
            self.logger.error(f"Failed to log detailed air quality: {e}")

    def log_weather_detailed(self, weather_data: Dict):
        """Log detailed weather data from hybrid sources"""
        try:
            temperature = weather_data.get('temperature', 0)
            source = weather_data.get('source', 'unknown')
            location = weather_data.get('location', 'Unknown')
            
            # Create details dict with all weather info
            details = {
                'feels_like': weather_data.get('feels_like'),
                'humidity': weather_data.get('humidity'),
                'pressure': weather_data.get('pressure'),
                'wind_speed': weather_data.get('wind_speed'),
                'wind_direction': weather_data.get('wind_direction'),
                'condition': weather_data.get('condition'),
                'precipitation_mm': weather_data.get('precipitation_mm'),
                'uv_index': weather_data.get('uv_index'),
            }
            
            # Log temperature with all details
            self.log_environmental_data('temperature', temperature, details, source, location)
            
            self.logger.debug(f"Logged weather data: Temp={temperature}°C, Source={source}, Location={location}")

        except Exception as e:
            self.logger.error(f"Failed to log detailed weather: {e}")

    def get_air_quality_history(self, hours: int = 24) -> List[Dict]:
        """Get air quality history for the last N hours"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT timestamp, value, details, source, location
                    FROM environmental_data
                    WHERE data_type = 'aqi'
                    AND timestamp >= datetime('now', '-{hours} hours')
                    ORDER BY timestamp DESC
                """
                )
                
                rows = cursor.fetchall()
                history = []
                for row in rows:
                    history.append({
                        'timestamp': row[0],
                        'aqi': row[1],
                        'details': json.loads(row[2]) if row[2] else {},
                        'source': row[3],
                        'location': row[4]
                    })
                
                return history

        except Exception as e:
            self.logger.error(f"Failed to get air quality history: {e}")
            return []

    def get_weather_history(self, hours: int = 24) -> List[Dict]:
        """Get weather history for the last N hours"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT timestamp, value, details, source, location
                    FROM environmental_data
                    WHERE data_type = 'temperature'
                    AND timestamp >= datetime('now', '-{hours} hours')
                    ORDER BY timestamp DESC
                """
                )
                
                rows = cursor.fetchall()
                history = []
                for row in rows:
                    details = json.loads(row[2]) if row[2] else {}
                    history.append({
                        'timestamp': row[0],
                        'temperature': row[1],
                        'humidity': details.get('humidity'),
                        'pressure': details.get('pressure'),
                        'condition': details.get('condition'),
                        'source': row[3],
                        'location': row[4]
                    })
                
                return history

        except Exception as e:
            self.logger.error(f"Failed to get weather history: {e}")
            return []

    def get_user_patterns(self, days: int = 7) -> List[Dict]:
        """Get user interaction patterns for ML training"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT action, color_r, color_g, color_b, brightness, hour, day_of_week, timestamp
                    FROM user_interactions
                    WHERE timestamp >= datetime('now', '-{days} days')
                    ORDER BY timestamp
                """
                )

                rows = cursor.fetchall()

                patterns = []
                for row in rows:
                    patterns.append(
                        {
                            "action": row[0],
                            "color": (
                                (row[1], row[2], row[3]) if row[1] is not None else None
                            ),
                            "brightness": row[4],
                            "hour": row[5],
                            "day_of_week": row[6],
                            "timestamp": row[7],
                        }
                    )

                return patterns

        except Exception as e:
            self.logger.error(f"Failed to get user patterns: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM user_interactions")
                user_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM environmental_data")
                env_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_logs")
                log_count = cursor.fetchone()[0]

                return {
                    "user_interactions": user_count,
                    "environmental_data": env_count,
                    "system_logs": log_count,
                    "database_size": (
                        os.path.getsize(self.db_path)
                        if os.path.exists(self.db_path)
                        else 0
                    ),
                }

        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30):
        """Remove old data to keep database size manageable"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    f"""DELETE FROM user_interactions WHERE timestamp < datetime('now', '-{days} days')"""
                )

                cursor.execute(
                    f"""DELETE FROM environmental_data WHERE timestamp < datetime('now', '-{days} days')"""
                )

                cursor.execute(
                    f"""DELETE FROM system_logs WHERE timestamp < datetime('now', '-{days} days')"""
                )

                cursor.execute("VACUUM")
                conn.commit()

                self.logger.info(f"Cleaned up data older than {days} days")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
