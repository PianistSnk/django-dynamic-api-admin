"""
API 模型基类
"""
from abc import abstractmethod
from django.db import models


class APIModel(models.Model):
    """API 模型基类 - 用户自定义模型继承此类"""
    
    black_fields = ['id']
    input_date = models.CharField(max_length=255, verbose_name='日期yyyymmdd')
    
    class Meta:
        abstract = True
        default_permissions = []
    
    @property
    @abstractmethod
    def urls(self) -> str:
        """返回 API 接口地址"""
        pass
    
    @property
    def cache_key(self) -> str:
        """返回 Redis 缓存键前缀（可选）"""
        return self.__class__.__name__.lower() + '_'
    
    def __str__(self):
        return str(self.id)


# -------------------- 便捷装饰器 --------------------

def api_model(urls: str, cache_key: str = None, black_fields: list = None):
    """
    API 模型装饰器
    
    用法:
        @api_model('/api/data/', 'data_cache_', ['password'])
        class MyData(APIModel):
            pass
    """
    def decorator(cls):
        # 添加 urls 属性
        cls.urls = property(lambda self: urls)
        
        # 添加 cache_key 属性
        if cache_key:
            cls.cache_key = property(lambda self: cache_key)
        
        # 添加 black_fields
        if black_fields:
            cls.black_fields = black_fields
        
        return cls
    
    return decorator
