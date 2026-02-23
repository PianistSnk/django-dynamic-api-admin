"""
Django Dynamic API Admin - 模型定义
"""

from django.db import models


class APIModel(models.Model):
    """API 模型基类（可选继承）"""
    
    black_fields = ['id']
    
    class Meta:
        abstract = True
        default_permissions = []
    
    @property
    def urls(self) -> str:
        return ''


def api_model(url: str, black_fields: list = None):
    """
    API 模型装饰器
    
    用法:
        @api_model('/api/users/', ['password'])
        class User:
            pass
    """
    def decorator(cls):
        cls.api_url = url
        if black_fields:
            cls.black_fields = black_fields
        return cls
    return decorator
