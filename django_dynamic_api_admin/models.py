from abc import abstractmethod
from django.db import models


class APIModel(models.Model):
    """API 模型基类"""
    
    black_fields = ['id']
    input_date = models.CharField(max_length=255, verbose_name='日期yyyymmdd')
    
    class Meta:
        abstract = True
        default_permissions = []
    
    @abstractmethod
    def urls(self):
        """返回 API 接口地址"""
        pass
    
    @abstractmethod
    def cache(self):
        """返回 Redis 缓存键前缀"""
        pass
    
    def __str__(self):
        return str(self.id)
