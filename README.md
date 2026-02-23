# 🚀 Django Dynamic API Admin

[![PyPI version](https://badge.fury.io/py/django-dynamic-api-admin.svg)](https://badge.fury.io/py/django-dynamic-api-admin)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-3.2+-green.svg)](https://www.djangoproject.com/)

一个简洁优雅的 Django Admin 组件，用于动态展示和管理 REST API 数据。无需编写模型，直接接入第三方 API！

## ✨ 特性

- 🔄 **零模型接入** - 无需创建 Django 模型，直接展示 API 数据
- 📦 **Redis 缓存** - 内置缓存机制，减少 API 调用
- 🔍 **搜索过滤** - 支持多字段组合搜索
- 📊 **智能排序** - 支持多字段任意排序
- 📄 **文件处理** - 支持 PDF 等文件在线预览/下载
- 🔐 **安全设计** - 输入过滤、缓存管理
- 📝 **日志记录** - 完整记录用户操作

## 🛠️ 安装

```bash
pip install django-dynamic-api-admin
```

## 🚀 快速开始

### 1. 创建模型

```python
# models.py
from django.db import models
from django_dynamic_api_admin.models import api_model


@api_model('/api/my-data/', 'my_data_', ['id'])
class MyAPIData(models.Model):
    class Meta:
        verbose_name = '我的API数据'
```

### 2. 创建 Admin

```python
# admin.py
from django.contrib import admin
from django_dynamic_api_admin.admin import APIAdmin
from .models import MyAPIData


@admin.register(MyAPIData)
class MyAPIAdmin(APIAdmin):
    list_per_page = 50
    paras_list = ['q', 'o', 'dt', 'p']
```

### 3. 完成！

访问 Admin 页面，API 数据会自动展示！

## 📚 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `list_per_page` | 每页数量 | 100 |
| `paras_list` | API 参数列表 | `['q', 'o', 'dt', 'p']` |
| `black_fields` | 排除字段 | `[]` |
| `cache_config` | Redis 配置 | 内置配置 |

## 🏗️ 项目结构

```
django_dynamic_api_admin/
├── __init__.py      # 入口
├── admin.py         # 核心类
├── base.py         # 抽象基类
├── cache.py        # Redis 缓存
├── models.py       # 模型基类
└── example/        # 使用示例
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 License

MIT License

---

如果这个项目对你有帮助，请 ⭐ Star 支持！
