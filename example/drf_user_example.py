"""
示例：Django REST Framework + Django Dynamic API Admin

这个示例展示了如何：
1. 创建 DRF User API
2. 用 django-dynamic-api-admin 管理这个 API
"""

# =====================
# 1. 安装依赖
# =====================
"""
pip install django djangorestframework django-dynamic-api-admin
"""

# =====================
# 2. Django Settings
# =====================

# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'django_dynamic_api_admin',
    'myapp',
]

# DRF 配置
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}


# =====================
# 3. 创建 DRF API
# =====================

# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """扩展用户模型"""
    phone = models.CharField(max_length=20, verbose_name='手机号', blank=True)
    avatar = models.URLField(verbose_name='头像', blank=True)
    bio = models.TextField(verbose_name='简介', blank=True)
    points = models.IntegerField(default=0, verbose_name='积分')
    status = models.CharField(
        max_length=20,
        choices=[('active', '活跃'), ('inactive', '未激活'), ('banned', '禁用')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username


# serializers.py
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'phone', 'avatar', 'bio', 'points', 'status', 
                  'is_staff', 'is_active', 'date_joined', 'created_at', 'updated_at']


# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """用户 CRUD API"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 支持搜索和过滤
        queryset = super().get_queryset()
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(phone__icontains=search)
            )
        
        # 过滤状态
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('api/', include(router.urls)),
]


# =====================
# 4. 用 django-dynamic-api-admin 管理
# =====================

# admin.py
from django.contrib import admin
from django_dynamic_api_admin.admin import APIAdmin
from django_dynamic_api_admin.models import api_model
from .models import User


# 方式1：使用装饰器
@api_model(
    urls='/api/users/',      # DRF API 地址
    cache_key='drf_users_',   # Redis 缓存键
    black_fields=['password', 'is_staff']  # 排除敏感字段
)
class UserAPI:
    """用于 API Admin 的虚拟模型"""
    pass


# 方式2：继承 APIModel
from django_dynamic_api_admin.models import APIModel


class UserAPIModel(APIModel):
    """用户 API 模型"""
    
    class Meta:
        verbose_name = '用户(API)'
    
    @property
    def urls(self):
        return '/api/users/'
    
    @property
    def cache_key(self):
        return 'drf_users_'


# 创建 Admin
@admin.register(UserAPIModel)
class UserAPIAdmin(APIAdmin):
    """用户 API 管理"""
    
    list_per_page = 20
    paras_list = ['search', 'status', 'o', 'p']
    
    # 排除敏感字段
    black_fields = ['password', 'is_staff']
    
    # 缓存配置
    cache_config = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
    }


# =====================
# 5. 效果
# =====================
"""
访问 Django Admin，你会看到：

用户管理 (API)
├── 列表页：显示所有用户
├── 搜索：支持用户名/邮箱/手机搜索
├── 过滤：按状态筛选
├── 排序：支持多字段排序
├── 分页：每页20条
└── 缓存：5分钟自动刷新

数据来源：DRF API (/api/users/)
缓存：Redis (drf_users_YYYYMMDD)
"""


# =====================
# 6. 进阶：自定义数据处理
# =====================

class CustomUserAPIAdmin(APIAdmin):
    """自定义用户管理"""
    
    def get_api_url(self, paras):
        """自定义 URL 构建"""
        base_url = '/api/users/'
        
        # 添加搜索参数
        if 'search' in paras:
            base_url += f'?search={paras["search"]}'
        
        # 添加状态过滤
        if 'status' in paras:
            sep = '&' if '?' in base_url else '?'
            base_url += f'{sep}status={paras["status"]}'
        
        return base_url
    
    def _build_queryset(self, data, fields, paras):
        """自定义数据处理"""
        # 添加计算字段
        for item in data:
            # 示例：添加会员等级
            if item.get('points', 0) >= 1000:
                item['level'] = 'VIP'
            elif item.get('points', 0) >= 100:
                item['level'] = 'Gold'
            else:
                item['level'] = 'Normal'
        
        return super()._build_queryset(data, fields, paras)


# =====================
# 7. 完整项目结构
# =====================

"""
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── myapp/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
└── requirements.txt
"""
