# -*- coding: utf-8 -*-

from hardware import HardwareController
from sensors import SensorManager
from lamp import LampController
from ml import MLManager
from database import DatabaseManager
from lumina.utils.base import Utils

# Version info
__version__ = "1.0.0"
__author__ = "Group E - VIP Smart Lamp Team"

# Make everything easily accessible
__all__ = [
    "HardwareController",
    "SensorManager",
    "LampController",
    "MLManager",
    "DatabaseManager",
    "Utils",
]
