"""
Django Dynamic API Admin - 抽象基类
"""

from abc import ABC, abstractmethod
from typing import List


class APIAdminBase(ABC):
    """API Admin 抽象基类"""
    
    @property
    @abstractmethod
    def api_url(self) -> str:
        """API 地址"""
        pass


class APIModel:
    """API 模型基类（可选使用）"""
    
    black_fields: List[str] = []
    
    @property
    def urls(self) -> str:
        """兼容旧版本"""
        return ''
