"""
Django API Admin
一个通用的 Django Admin 后台管理组件，用于动态展示和管理 REST API 数据。
"""

from .admin import (
    APIAdmin,
    APINoDataAdmin,
    APIAjaxAdmin,
    BaseAdmin,
    BaseAjaxAdmin,
    YYDMAdmin,
)
from .models import APIModel

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "APIAdmin",
    "APINoDataAdmin",
    "APIAjaxAdmin",
    "BaseAdmin",
    "BaseAjaxAdmin", 
    "YYDMAdmin",
    "APIModel",
]
