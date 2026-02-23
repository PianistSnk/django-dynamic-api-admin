"""
API Admin 核心类
"""
import json
import logging
from typing import Dict, List, Any, Optional
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.utils.safestring import mark_safe

from .base import BaseAPIAdmin
from .cache import CacheManager

logger = logging.getLogger(__name__)


class APIChangeList:
    """定制化列表"""
    pass


class MyQuerySet(models.QuerySet):
    """可克隆的 QuerySet"""
    def _clone(self):
        import copy
        return copy.copy(self)


class APIAdmin(BaseAPIAdmin):
    """通用 API 管理类"""
    
    change_list_template = 'admin/change_list_html.html'
    list_display_links = None
    
    # 内部状态
    json_to_filter: Optional[List] = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = CacheManager(self.cache_config)
    
    # -------------------- 核心方法 --------------------
    
    def get_api_url(self, paras: Dict) -> str:
        """获取 API URL - 子类需要重写"""
        return getattr(self.model, 'urls', lambda: '')()
    
    def get_api_data(self, request) -> tuple:
        """获取 API 数据"""
        from django.contrib import messages
        import requests
        
        # 获取参数
        paras = self._get_params(request)
        
        # 尝试从缓存获取
        cache_key = self.get_cache_key(paras)
        data = self.cache.get(cache_key) if cache_key else None
        
        if data:
            logger.info(f"从缓存获取数据: {cache_key}")
        else:
            # 调用 API
            url = self.get_api_url(paras)
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {}).get('items', [])
                    # 存入缓存
                    if data and cache_key:
                        self.cache.set(cache_key, data, ttl=300)  # 缓存5分钟
                else:
                    data = []
                    messages.add_message(request, messages.ERROR, f'API请求失败: {response.status_code}')
            except requests.RequestException as e:
                data = []
                messages.add_message(request, messages.ERROR, f'API请求异常: {str(e)}')
        
        if not data:
            return MyQuerySet(model=self.model), ['id']
        
        # 处理数据
        fields = self._extract_fields(data)
        queryset = self._build_queryset(data, fields, paras)
        
        # 记录日志
        self._log_action(request)
        
        # 缓存列表显示字段
        self.api_list = fields
        
        return queryset, fields
    
    def get_list_display(self, request) -> List:
        """获取列表显示字段"""
        if not self.api_list:
            self.api_data, self.api_list = self.get_api_data(request)
        return self.api_list
    
    def get_changelist(self, request, **kwargs):
        return APIChangeList
    
    def get_queryset(self, request):
        return self.api_data
    
    def get_object(self, request, object_id, from_field=None):
        """获取单个对象"""
        user_key = f"{request.user.username}_{object_id}"
        return self._user_cache.get(user_key)
    
    # -------------------- 辅助方法 --------------------
    
    def _get_params(self, request) -> Dict:
        """获取请求参数"""
        from urllib.parse import parse_qs
        
        paras = dict(request.GET.items())
        # 清理 URL 编码
        return {k[4:] if k.startswith('amp;') else k: v for k, v in paras.items()}
    
    def _extract_fields(self, data: List) -> List:
        """提取字段列表"""
        if not data:
            return ['id']
        fields = list(data[0].keys())
        black = getattr(self.model, 'black_fields', []) or self.black_fields
        return [f for f in fields if f not in black]
    
    def _build_queryset(self, data: List, fields: List, paras: Dict) -> MyQuerySet:
        """构建 QuerySet"""
        # 排序
        if 'o' in paras:
            data = self._sort_data(data, fields, paras['o'])
        
        # 搜索过滤
        search_filters = {
            k: v for k, v in paras.items() 
            if k not in ['q', 'o', 'p'] and k in fields
        }
        
        if search_filters:
            data = [
                item for item in data
                if all(
                    str(item.get(k, '')) == v 
                    for k, v in search_filters.items()
                )
            ]
        
        # 分页
        page = int(paras.get('p', 1))
        start = self.list_per_page * (page - 1)
        end = start + self.list_per_page
        data = data[start:end]
        
        # 构建模型
        mymodels = []
        for i, item in enumerate(data, 1):
            obj = self.model(id=i, pk=i)
            for field in fields:
                if field in item:
                    setattr(obj, field, item[field])
            mymodels.append(obj)
        
        qs = MyQuerySet(model=self.model)
        qs._result_cache = mymodels
        return qs
    
    def _sort_data(self, data: List, fields: List, order_str: str) -> List:
        """排序数据"""
        if not order_str:
            return data
        
        orders = order_str.split('.')
        if not orders:
            return data
        
        def get_sort_key(item):
            values = []
            for idx in orders:
                idx = abs(int(idx)) if idx.lstrip('-').isdigit() else 0
                if idx < len(fields):
                    val = item.get(fields[idx], '')
                    # 尝试转换为数字
                    try:
                        if isinstance(val, str):
                            val = float(val.replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                    values.append(val)
                else:
                    values.append('')
            return values
        
        # 升序/降序
        reverse = orders[0].startswith('-') if orders else False
        
        try:
            return sorted(data, key=get_sort_key, reverse=reverse)
        except Exception:
            return data
    
    def _log_action(self, request):
        """记录操作日志"""
        try:
            LogEntry.objects.create(
                action_time=__import__('datetime').datetime.now(),
                user=request.user,
                action_flag=4,  # VIEW
                content_type=ContentType.objects.get(model=self.model.__name__)
            )
        except Exception:
            pass
    
    # -------------------- UI 组件 --------------------
    
    @admin.display(description=mark_safe('<input type="checkbox" id="action-toggle">'))
    def action_checkbox(self, obj):
        return helpers.checkbox.render("_selected_action", str(obj.id))
    
    def get_search_results(self, request, queryset, search_term):
        return queryset, False
    
    def get_list_filter(self, request):
        return []


class APIFilter:
    """自定义过滤器"""
    
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field = field
        self.request = request
        self.params = params
        self.model = model
        self.model_admin = model_admin
        self.field_path = field_path
        self.empty_value_display = model_admin.get_empty_value_display()
        
        # 获取可选值
        queryset = getattr(model_admin, 'json_to_filter', []) or []
        values = []
        seen = set()
        
        for obj in queryset:
            value = obj.get(field_path, '')
            if value and value not in seen:
                seen.add(value)
                values.append((value, value))
        
        self.lookup_choices = values


# -------------------- 文件下载 --------------------

def view_or_download(url: str, file_type: str, name: str, user, filename: str = None):
    """文件预览/下载"""
    from io import BytesIO
    from django.http import FileResponse
    import:
        response = requests
    
    try requests.get(url, timeout=30)
        content = response.content
        
        pdf_file = BytesIO()
        pdf_file.write(content)
        pdf_file.seek(0)
        
        content_type = f'application/{file_type}'
        
        if filename:
            # 下载
            def quote(s):
                return ''.join(['%{:02X}'.format(b) for b in s.encode('utf-8')])
            
            resp = FileResponse(pdf_file, content_type=content_type)
            resp['Content-Disposition'] = f'attachment;filename="{quote(filename)}.{file_type}"'
            
            # 记录日志
            LogEntry.objects.create(
                action_time=__import__('datetime').datetime.now(),
                user=user,
                action_flag=6,  # DOWNLOAD
                object_repr=f'{filename}.{file_type}',
                content_type=ContentType.objects.get(model=name)
            )
        else:
            # 预览
            resp = FileResponse(pdf_file, content_type=content_type)
            resp['Content-Disposition'] = 'inline'
        
        return resp
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        return None
