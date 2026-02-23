# 🚀 Django Dynamic API Admin

[![PyPI](https://badge.fury.io/py/django-dynamic-api-admin.svg)](https://pypi.org/project/django-dynamic-api-admin/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

无需编写 Django Model，直接用外部 API 数据管理

## ✨ 核心功能

- 🔄 **零模型接入** - 无需创建 Django 模型，直接展示 API 数据
- 🔍 **搜索过滤** - 支持多字段组合搜索
- 📊 **智能排序** - 支持多字段任意排序
- 📄 **文件处理** - 支持 PDF 等文件在线预览/下载

## 🛠️ 安装

```bash
pip install django-dynamic-api-admin
```

## 🚀 快速开始

```python
# admin.py
from django.contrib import admin
from django_dynamic_api_admin import APIAdmin, api_model


@api_model('/api/users/')
class UserAPI:
    pass


@admin.register(UserAPI)
class UserAPIAdmin(APIAdmin):
    api_url = '/api/users/'
    black_fields = ['password']
```

访问 Admin 页面，API 数据自动展示！

## 📖 文档

详见 [example/](example/) 目录

## License

MIT
