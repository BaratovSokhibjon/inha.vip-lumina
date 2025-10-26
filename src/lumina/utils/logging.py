"""
Logging configuration for Lumina
"""

import logging

def setup_logging(log_level="INFO"):
    """Setup logging for the application"""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
