"""
Django Dynamic API Admin
无需编写 Django Model，直接用外部 API 数据管理
"""

from .admin import APIAdmin
from .models import APIModel, api_model
from .base import APIAdminBase

__version__ = "2.1.0"
__author__ = "PianistSnk"

__all__ = [
    "APIAdmin",
    "APIModel",
    "api_model",
    "APIAdminBase",
]
