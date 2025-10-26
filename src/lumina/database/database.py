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

                # Environmental data table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS environmental_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        data_type TEXT NOT NULL,
                        value REAL,
                        details TEXT
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
        self, data_type: str, value: float, details: Dict = None
    ):
        """Log environmental sensor data"""
        try:
            details_json = json.dumps(details) if details else None

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO environmental_data (data_type, value, details)
                    VALUES (?, ?, ?)
                """,
                    (data_type, value, details_json),
                )
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log environmental data: {e}")

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
