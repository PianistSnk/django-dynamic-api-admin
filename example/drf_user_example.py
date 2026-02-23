"""
示例：Django REST Framework + Django Dynamic API Admin

核心功能：无需编写 Django Model，直接用 DRF API 数据管理
"""

# =====================
# 1. 创建 DRF User API
# =====================

# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    points = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[('active', '活跃'), ('inactive', '未激活')],
        default='active'
    )


# serializers.py
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'points', 'status']


# views.py
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# =====================
# 2. 用 django-dynamic-api-admin 管理
# =====================

# admin.py
from django.contrib import admin
from django_dynamic_api_admin.admin import APIAdmin
from django_dynamic_api_admin.models import api_model


# 零模型接入！直接用 API URL
@api_model('/api/users/')
class UserAPI:
    """虚拟模型，只需定义 API 地址"""
    pass


@admin.register(UserAPI)
class UserAPIAdmin(APIAdmin):
    """用户 API 管理"""
    list_per_page = 20
    black_fields = ['password']  # 排除敏感字段


# =====================
# 3. 核心优势
# =====================
"""
对比：

传统方式：
1. 写 Django Model
2. 写 Serializer  
3. 写 ViewSet
4. 配置 URL
5. 在 Admin 注册

django-dynamic-api-admin 方式：
1. 定义 API 地址
2. 注册 Admin

就两步！
"""
