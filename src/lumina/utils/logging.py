"""
Logging configuration for Lumina
"""

import logging

def setup_logging(log_file_path=None, log_level="INFO"):
    """Setup logging for the application"""
    handlers = []

    if log_file_path:
        handlers.append(logging.FileHandler(log_file_path))

    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
