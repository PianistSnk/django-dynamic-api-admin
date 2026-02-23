"""
Django Dynamic API Admin 使用示例

安装:
    pip install django-dynamic-api-admin

使用:
"""

# 1. 创建 API 模型
# ==============

from django.db import models
from django_dynamic_api_admin.models import APIModel


class StockData(APIModel):
    """股票数据模型"""
    
    class Meta:
        verbose_name = '股票数据'
        verbose_name_plural = '股票数据'
        black_fields = ['id', 'password']  # 排除字段
    
    @property
    def urls(self):
        return '/api/v1/stock/'
    
    @property
    def cache_key(self):
        return 'stock_data_'


# 2. 使用装饰器（更简洁）
# ======================

from django_dynamic_api_admin.models import api_model


@api_model('/api/v1/stock/', 'stock_', ['id'])
class StockData2(models.Model):
    """股票数据"""
    
    class Meta:
        verbose_name = '股票数据'
        verbose_name_plural = '股票数据'
    
    # 不需要实现 urls 和 cache_key，装饰器会自动处理


# 3. 创建 Admin
# =============

from django.contrib import admin
from django_dynamic_api_admin.admin import APIAdmin
from .models import StockData


@admin.register(StockData)
class StockDataAdmin(APIAdmin):
    """股票数据管理"""
    
    # 每页显示数量
    list_per_page = 50
    
    # API 参数列表
    paras_list = ['q', 'o', 'dt', 'p']
    
    # Redis 缓存配置
    cache_config = {
        'host': 'localhost',
        'port': 16379,
        'db': 0,
        'password': None  # 生产环境使用环境变量
    }


# 4. 高级用法：自定义数据处理
# ==========================

class CustomAPIAdmin(APIAdmin):
    """自定义 API 管理类"""
    
    def get_api_url(self, paras):
        """自定义 URL 构建"""
        base_url = super().get_api_url(paras)
        # 添加自定义参数
        return f"{base_url}&custom_param=value"
    
    def get_api_data(self, request):
        """自定义数据获取"""
        queryset, fields = super().get_api_data(request)
        # 在这里对数据进行处理
        # 例如：添加计算字段、转换格式等
        return queryset, fields


# 5. Django REST Framework 结合
# ============================

# urls.py
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
]


# 6. 生产环境配置建议
# =================

"""
settings.py 配置建议:

# Redis 配置（使用环境变量）
CACHE_CONFIG = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 16379)),
    'password': os.environ.get('REDIS_PASSWORD'),
    'db': 0,
}

# API Admin 配置
API_ADMIN_CONFIG = {
    'DEFAULT_LIST_PER_PAGE': 50,
    'DEFAULT_CACHE_TTL': 300,  # 5分钟
}

# 安全建议:
# 1. 不要在前端暴露敏感字段（使用 black_fields）
# 2. API 接口添加认证
# 3. 使用 HTTPS
# 4. 限制 IP 访问
# 5. 定期清理缓存
"""
