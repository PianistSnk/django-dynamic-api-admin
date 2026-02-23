"""
抽象基类
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from django.db import models
from django.contrib import admin


class APIModel(models.Model):
    """API 模型基类"""
    
    black_fields: List[str] = []
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
    @abstractmethod
    def cache_key(self) -> str:
        """返回 Redis 缓存键前缀"""
        pass


class BaseAPIAdmin(admin.ModelAdmin, ABC):
    """通用 API 管理基类"""
    
    # 配置项
    api_data: Optional[Any] = None
    api_list: Optional[List] = None
    list_per_page: int = 100
    paras_list: List[str] = ['q', 'o', 'dt', 'p']
    black_fields: List[str] = []
    
    # 缓存配置
    cache_config: Dict = {
        'host': 'localhost',
        'port': 16379,
        'db': 0,
        'password': None
    }
    
    # 用户搜索结果缓存
    _user_cache: Dict[str, Any] = {}
    
    @abstractmethod
    def get_api_url(self, paras: Dict) -> str:
        """获取 API URL"""
        pass
    
    def get_cache_key(self, paras: Dict) -> str:
        """获取缓存键"""
        dt = paras.get('dt', '')
        if dt:
            from datetime import datetime
            try:
                dt = datetime.strptime(dt.split()[1:4], ['%b', '%d', '%Y']).strftime('%Y%m%d')
            except:
                dt = ''
        return f"{self.model.cache_key}{dt}" if hasattr(self.model, 'cache_key') else ''
    
    def parse_date(self, dt: str) -> str:
        """解析日期格式"""
        if not dt:
            return ''
        from datetime import datetime
        try:
            # "Jan 01 2026" -> "20260101"
            parts = dt.split()
            if len(parts) >= 3:
                return datetime.strptime(f"{parts[1]} {parts[2]} {parts[3]}", '%b %d %Y').strftime('%Y%m%d')
        except:
            pass
        return ''
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
