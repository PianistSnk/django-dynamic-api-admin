"""
示例：如何使用 Django API Admin
"""

# 1. 安装
# pip install django-api-admin

# 2. 在 Django 项目中使用
# settings.py
INSTALLED_APPS = [
    ...
    'django_api_admin',
    'simpleui',  # 可选
    'your_app',
]

# 3. 创建 API 模型
# your_app/models.py
from django.db import models
from django_api_admin.models import APIModel


class StockData(APIModel):
    """股票数据示例"""
    
    class Meta:
        verbose_name = '股票数据'
        verbose_name_plural = '股票数据'
        cache = 'stock_data_'  # Redis 缓存键前缀
        black_fields = ['id', 'created_at']  # 排除的字段
    
    def urls(self):
        # 返回 API 接口地址
        return '/api/v1/stock/'
    
    def cache(self):
        return self._meta.cache


# 4. 创建 Admin
# your_app/admin.py
from django.contrib import admin
from django_api_admin.admin import APIAdmin
from .models import StockData


@admin.register(StockData)
class StockDataAdmin(APIAdmin):
    """股票数据管理"""
    
    # 每页显示数量
    list_per_page = 10000
    
    # API 参数列表
    paras_list = ['q', 'o', 'dt', 'p']
    
    # 搜索字段
    search_fields = ['stock_code', 'stock_name']
    
    # 排除字段
    black_fields = ['id']
    
    # Redis 配置（可选）
    cache_config = {
        'host': 'localhost',
        'port': 16379,
        'db': 0,
        'password': None  # 如需密码认证
    }
    
    # 启用操作（可选）
    actions = ['export_selected']


# 5. 高级用法：自定义 API 转换
class CustomAPIAdmin(APIAdmin):
    """自定义 API 管理类"""
    
    def get_api_urls(self, paras, request):
        """自定义 API URL 构建"""
        base_url = super().get_api_urls(paras, request)
        # 添加自定义参数
        return f"{base_url}&custom_param=value"
    
    def get_redis_data(self, paras):
        """自定义缓存逻辑"""
        # 实现自己的缓存策略
        return super().get_redis_data(paras)
    
    def get_api_data(self, request):
        """自定义数据处理"""
        queryset, fields = super().get_api_data(request)
        # 可以在这里对数据进行二次处理
        return queryset, fields


# 6. 与 Django REST Framework 结合
# urls.py
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Admin（如需独立 URL）
    # path('api-admin/', APIAdminSite().urls),
]


# 7. 部署建议
"""
生产环境配置：

1. Redis 配置
   - 使用密码认证
   - 配置合理的过期时间
   - 开启持久化

2. 性能优化
   - 合理设置 list_per_page
   - 启用 Redis 缓存
   - 使用索引优化查询

3. 安全
   - API 接口添加认证
   - 限制 IP 访问
   - 敏感数据脱敏
"""
