# -*- coding: utf-8 -*-

from .hardware_config import HardwareConfig
from .settings import Settings

# Make configs easily accessible
hardware = HardwareConfig()
settings = Settings()

__all__ = ['hardware', 'settings', 'HardwareConfig', 'Settings']