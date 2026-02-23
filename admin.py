"""
Django Dynamic API Admin - 核心类
无需编写 Django Model，直接用外部 API 数据管理
"""

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

logger = logging.getLogger(__name__)


class APIChangeList:
    """定制化列表"""
    pass


class MyQuerySet(models.QuerySet):
    """可克隆的 QuerySet"""
    def _clone(self):
        import copy
        return copy.copy(self)


class APIAdmin(admin.ModelAdmin):
    """
    通用 API 管理类
    
    核心功能：无需编写 Django Model，直接管理外部 API 数据
    """
    
    change_list_template = 'admin/change_list_html.html'
    list_display_links = None
    
    # 配置项
    api_url: str = ''  # API 地址，子类必须定义
    list_per_page: int = 100
    paras_list: List[str] = ['q', 'o', 'dt', 'p']
    black_fields: List[str] = []
    
    # 内部状态
    json_to_filter: Optional[List] = None
    api_list: Optional[List] = None
    
    # -------------------- 核心方法 --------------------
    
    def get_api_url(self, paras: Dict) -> str:
        """获取 API URL"""
        return self.api_url
    
    def get_api_data(self, request) -> tuple:
        """获取 API 数据"""
        import requests
        
        # 获取参数
        paras = self._get_params(request)
        
        # 构建 URL
        url = self._build_url(paras)
        
        # 调用 API
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {}).get('items', [])
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
        
        self.api_list = fields
        return queryset, fields
    
    def get_list_display(self, request) -> List:
        """获取列表显示字段"""
        if not self.api_list:
            self.get_api_data(request)
        return self.api_list
    
    def get_changelist(self, request, **kwargs):
        return APIChangeList
    
    def get_queryset(self, request):
        return self.api_data
    
    # -------------------- 辅助方法 --------------------
    
    def _get_params(self, request) -> Dict:
        """获取请求参数"""
        paras = dict(request.GET.items())
        return {k[4:] if k.startswith('amp;') else k: v for k, v in paras.items()}
    
    def _build_url(self, paras: Dict) -> str:
        """构建 API URL"""
        url = self.get_api_url(paras)
        # 添加查询参数
        params = []
        for key in self.paras_list:
            if key in paras and paras[key]:
                params.append(f"{key}={paras[key]}")
        if params:
            sep = '&' if '?' in url else '?'
            url += sep + '&'.join(params)
        return url
    
    def _extract_fields(self, data: List) -> List:
        """提取字段列表"""
        if not data:
            return ['id']
        fields = list(data[0].keys())
        return [f for f in fields if f not in self.black_fields]
    
    def _build_queryset(self, data: List, fields: List, paras: Dict) -> MyQuerySet:
        """构建 QuerySet"""
        # 排序
        if 'o' in paras:
            data = self._sort_data(data, fields, paras['o'])
        
        # 搜索过滤
        search_filters = {k: v for k, v in paras.items() 
                        if k not in ['q', 'o', 'p'] and k in fields}
        
        if search_filters:
            data = [item for item in data if all(
                str(item.get(k, '')) == v for k, v in search_filters.items()
            )]
        
        # 分页
        page = int(paras.get('p', 1))
        start = self.list_per_page * (page - 1)
        data = data[start:start + self.list_per_page]
        
        # 构建对象
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
        
        def get_key(item):
            values = []
            for idx in orders:
                idx = abs(int(idx)) if idx.lstrip('-').isdigit() else 0
                if idx < len(fields):
                    val = item.get(fields[idx], '')
                    try:
                        if isinstance(val, str):
                            val = float(val.replace(',', ''))
                    except:
                        pass
                    values.append(val)
                else:
                    values.append('')
            return values
        
        reverse = orders[0].startswith('-') if orders else False
        try:
            return sorted(data, key=get_key, reverse=reverse)
        except:
            return data
    
    def _log_action(self, request):
        """记录操作日志"""
        try:
            from datetime import datetime
            LogEntry.objects.create(
                action_time=datetime.now(),
                user=request.user,
                action_flag=4,
                content_type=ContentType.objects.get(model=self.model.__name__)
            )
        except:
            pass
    
    # -------------------- UI 组件 --------------------
    
    @admin.display(description=mark_safe('<input type="checkbox" id="action-toggle">'))
    def action_checkbox(self, obj):
        return helpers.checkbox.render("_selected_action", str(obj.id))
    
    def get_search_results(self, request, queryset, search_term):
        return queryset, False
    
    def get_list_filter(self, request):
        return []
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
