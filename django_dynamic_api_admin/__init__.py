"""
Django Dynamic API Admin
一个简洁优雅的 Django Admin 组件，用于动态展示和管理 REST API 数据。
"""

from .admin import APIAdmin, APIFilter, view_or_download
from .base import BaseAPIAdmin
from .models import APIModel, api_model
from .cache import CacheManager

__version__ = "2.0.0"
__author__ = "PianistSnk"

__all__ = [
    "APIAdmin",
    "APIFilter",
    "BaseAPIAdmin",
    "APIModel",
    "api_model",
    "CacheManager",
    "view_or_download",
]
