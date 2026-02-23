import datetime
import json
import locale
from io import BytesIO

import redis
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.decorators import display
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import FileResponse
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.utils.safestring import mark_safe

try:
    from more_admin_filters import MultiSelectDropdownFilter
except ImportError:
    MultiSelectDropdownFilter = None

try:
    from simpleui.admin import AjaxAdmin
except ImportError:
    AjaxAdmin = object


def convert(value):
    """转换值为可排序的格式"""
    if not isinstance(value, str):
        return value
    
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(value, fmt).timestamp()
        except (ValueError, TypeError):
            continue
    
    try:
        return float(value.replace(",", ""))
    except (ValueError, TypeError):
        return float('-inf') if value == " " else value


def quote(s):
    """URL 编码文件名"""
    return ''.join(['%{:02X}'.format(b) for b in s.encode('utf-8')])


def view_or_download(urls, type, name, user, filename=None):
    """文件预览/下载"""
    import requests
    
    response = requests.get(urls)
    pdf_data = response.content
    pdf_file = BytesIO()
    pdf_file.write(pdf_data)
    pdf_file.seek(0)
    
    content_type = f'application/{type}'
    if filename:
        response = FileResponse(
            pdf_file, 
            content_type=content_type,
            filename=f"{quote(filename)}.{type}"
        )
        response['Content-Disposition'] = f'attachment;filename="{quote(filename)}.{type}"'
        LogEntry.objects.create(
            action_time=datetime.datetime.now(),
            user=user,
            action_flag=6,
            object_repr=f'{filename}.{type}',
            content_type=ContentType.objects.get(model=name)
        )
    else:
        response = FileResponse(pdf_file, content_type=content_type)
        response['Content-Disposition'] = 'inline'
    
    return response


class APIChangeList:
    """定制化列表"""
    pass


class MyQuerySet(models.QuerySet):
    """可克隆的 QuerySet"""
    def _clone(self):
        import copy
        c = copy.copy(self)
        return c


class APIAdmin(admin.ModelAdmin):
    """通用 API 管理类"""
    
    change_list_template = 'admin/change_list_html.html'
    api_data = None
    api_list = None
    export_list = None
    list_per_page = 20000
    search_fields = ['input_date']
    list_display_links = None
    paras_list = ['q', 'o', 'dt', 'p']
    user_search_result = {}
    json_to_filter = None
    
    # 可配置项
    cache_config = {
        'host': 'localhost',
        'port': 16379,
        'db': 0,
        'password': None
    }
    
    def get_object(self, request, object_id, from_field=None):
        qs = list(self.user_search_result.get(request.user.username, []))
        for i in qs:
            if i.id == int(object_id):
                return i
        return None
    
    def response_action(self, request, queryset):
        """处理批量操作"""
        try:
            action_index = int(request.POST.get("index", 0))
        except ValueError:
            action_index = 0
        
        data = request.POST.copy()
        data.pop("_selected_action", None)
        data.pop("index", None)
        
        try:
            data.update({"action": data.getlist("action")[action_index]})
        except IndexError:
            pass
        
        action_form = self.action_form(data, auto_id=None)
        action_form.fields["action"].choices = self.get_action_choices(request)
        
        if not action_form.is_valid():
            msg = _("No action selected.")
            self.message_user(request, msg, messages.WARNING)
            return None
        
        action = action_form.cleaned_data["action"]
        select_across = action_form.cleaned_data["select_across"]
        func = self.get_actions(request)[action][0]
        
        selected = request.POST.getlist("_selected_action")
        if not selected and not select_across:
            msg = _("Items must be selected to perform actions.")
            self.message_user(request, msg, messages.WARNING)
            return None
        
        # 构建 QuerySet
        _queryset = []
        for i in queryset:
            if str(i.id) in selected or select_across:
                _queryset.append(i)
        
        mymodels_qs = MyQuerySet(model=self.model)
        mymodels_qs._result_cache = _queryset
        
        response = func(self, request, mymodels_qs)
        
        if isinstance(response, HttpResponseBase):
            return response
        return HttpResponseRedirect(request.get_full_path())
    
    @display(description=mark_safe('<input type="checkbox" id="action-toggle">'))
    def action_checkbox(self, obj):
        return helpers.checkbox.render("_selected_action", str(obj.id))
    
    def get_list_filter(self, request):
        if not self.api_list:
            return []
        return [(api, APIFilter) for api in self.api_list]
    
    def get_search_results(self, request, queryset, search_term):
        return queryset, False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_changelist(self, request, **kwargs):
        return APIChangeList
    
    def get_queryset(self, request):
        return self.api_data
    
    def get_api_urls(self, paras, request):
        """获取 API URL - 子类需要重写"""
        dt = paras.get("dt", "")
        if dt:
            dt = " ".join(dt.split(' ')[1:4])
            try:
                dt = datetime.datetime.strptime(dt, '%b %d %Y').strftime('%Y%m%d')
            except ValueError:
                dt = ''
        return self.model.urls + dt
    
    def get_redis_client(self):
        """获取 Redis 客户端"""
        return redis.Redis(
            host=self.cache_config.get('host', 'localhost'),
            port=self.cache_config.get('port', 16379),
            db=self.cache_config.get('db', 0),
            password=self.cache_config.get('password')
        )
    
    def get_redis_data(self, paras):
        """从 Redis 获取缓存数据"""
        if not self.model.cache:
            return None
        
        try:
            r = self.get_redis_client()
        except Exception:
            return None
        
        dt = paras.get("dt", "")
        if dt:
            dt = " ".join(dt.split(' ')[1:4])
            try:
                dt = datetime.datetime.strptime(dt, '%b %d %Y').strftime('%Y%m%d')
            except ValueError:
                dt = datetime.date.today().strftime('%Y%m%d')
        
        try:
            redis_values = r.get(f'{self.model.cache}{dt}')
            if redis_values:
                return json.loads(redis_values.decode('utf-8'))
        except Exception:
            pass
        
        return None
    
    def get_api_data(self, request):
        """获取 API 数据"""
        import requests
        
        paras = dict(request.GET.items())
        # 清理 URL 编码
        paras = {k[4:] if k.startswith('amp;') else k: v for k, v in paras.items()}
        
        # 处理排序
        order_list = paras.get('o', '').split('.') if 'o' in paras else []
        
        # 尝试从缓存获取
        data = self.get_redis_data(paras)
        
        if data:
            self.json_to_filter = data
        else:
            # 调用 API
            response = requests.get(self.get_api_urls(paras, request))
            if response.status_code == 200:
                data = json.loads(response.content)
                if 'data' in data and 'items' in data['data']:
                    data = data['data']['items']
                    self.json_to_filter = data
                else:
                    data = []
            else:
                data = []
                try:
                    content = json.loads(response.content)
                    if 'message' in content:
                        messages.add_message(request, messages.ERROR, content['message'])
                except:
                    messages.add_message(request, messages.ERROR, '查询有误')
        
        if not data:
            return MyQuerySet(model=self.model), ['id']
        
        # 获取字段
        fields = list(data[0].keys())
        fields = [i for i in fields if i not in self.model.black_fields]
        
        # 排序
        if order_list:
            data = self._sort_data(data, fields, order_list, request)
        
        # 动态添加字段
        for field_name in fields:
            if not hasattr(self.model, field_name):
                field = models.CharField(max_length=255)
                self.model.add_to_class(field_name, field)
        
        # 构建模型对象
        mymodels = self._build_models(data, fields, paras)
        
        # 记录日志
        try:
            LogEntry.objects.create(
                action_time=datetime.datetime.now(),
                user=request.user,
                action_flag=4,
                content_type=ContentType.objects.get(model=self.model.__name__)
            )
        except:
            pass
        
        self.user_search_result[request.user.username] = mymodels
        
        # 分页
        if 'p' in paras:
            page = int(paras['p'])
            mymodels = mymodels[self.list_per_page * (page - 1):self.list_per_page * page]
        
        return mymodels, fields
    
    def _sort_data(self, data, fields, order_list, request):
        """排序数据"""
        locale.setlocale(locale.LC_ALL, "")
        sort_keys = []
        sort_orders = []
        
        for i in order_list:
            field_idx = abs(int(i))
            if field_idx < len(fields):
                sort_keys.append(fields[field_idx])
                sort_orders.append(1 if not i.startswith('-') else -1)
        
        if not sort_keys:
            return data
        
        try:
            data = sorted(data, key=lambda x: tuple(
                sort_orders[j] * convert(x.get(sort_keys[j], ''))
                if isinstance(convert(x.get(sort_keys[j], '')), (int, float))
                else convert(x.get(sort_keys[j], ''))
                for j in range(len(sort_keys))
            ))
        except Exception as e:
            messages.add_message(request, messages.INFO, '此列暂时无法排序')
        
        return data
    
    def _build_models(self, data, fields, paras):
        """构建模型对象"""
        # 添加参数字段
        for field_name in self.paras_list:
            if field_name not in ['q', 'o'] and not hasattr(self.model, field_name):
                field = models.CharField(max_length=255)
                self.model.add_to_class(field_name, field)
        
        # 过滤搜索条件
        search_filters = {k: v for k, v in paras.items() 
                        if k not in ['q', 'o', 'p'] and k in fields}
        
        mymodels = []
        for i, item in enumerate(data, start=1):
            # 搜索过滤
            if search_filters:
                if not all(
                    field_name in item and str(item[field_name]) == search_filters[field_name]
                    for field_name in search_filters
                ):
                    continue
            
            mymodel = self.model(id=i, pk=i)
            for field_name in fields:
                if field_name in item:
                    setattr(mymodel, field_name, item[field_name])
            mymodels.append(mymodel)
        
        mymodels_qs = MyQuerySet(model=self.model)
        mymodels_qs._result_cache = mymodels
        return mymodels_qs
    
    def get_list_display(self, request):
        if not self.api_list:
            self.api_data, self.api_list = self.get_api_data(request)
            self.export_list = self.api_list
        return self.api_list


class APIFilter:
    """自定义过滤器"""
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field = field
        self.request = request
        self.params = params
        self.model = model
        self.model_admin = model_admin
        self.field_path = field_path
        self.lookup_kwarg = field_path
        self.lookup_kwarg_isnull = f"{field_path}__isnull"
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val_isnull = params.get(self.lookup_kwarg_isnull)
        self.empty_value_display = model_admin.get_empty_value_display()
        
        # 获取可选值
        queryset = model_admin.json_to_filter or []
        values = []
        for obj in queryset:
            value = obj.get(field_path, '')
            if isinstance(value, str):
                value = '、'.join(sorted(value.split('、')))
            if value and (value, value) not in values:
                values.append((value, value))
        self.lookup_choices = values


class APINoDataAdmin(APIAdmin):
    """无数据管理类"""
    def get_api_data(self, request):
        import requests
        
        paras = dict(request.GET.items())
        order_list = paras.get('o', '').split('.') if 'o' in paras else []
        
        if not paras:
            return MyQuerySet(model=self.model), ['id']
        
        # 尝试从缓存获取
        data = self.get_redis_data(paras)
        
        if data:
            self.json_to_filter = data
        else:
            response = requests.get(self.get_api_urls(paras, request))
            if response.status_code == 200:
                data = json.loads(response.content)
                if 'data' in data and 'items' in data['data']:
                    data = data['data']['items']
                    self.json_to_filter = data
                else:
                    data = []
            else:
                data = []
        
        if not data:
            return MyQuerySet(model=self.model), ['id']
        
        fields = list(data[0].keys()) if data else ['id']
        fields = [i for i in fields if i not in self.model.black_fields]
        
        # 排序和构建（与父类相同逻辑简略）
        mymodels = self._build_models(data, fields, paras)
        
        return mymodels, fields


if AjaxAdmin:
    class APIAjaxAdmin(AjaxAdmin, APIAdmin):
        """带 Ajax 支持的管理类"""
        def _get_queryset(self, request):
            post = request.POST
            action = post.get("_action")
            selected = post.get("_selected")
            select_across = post.get("select_across")
            
            if hasattr(self, action):
                queryset = self.user_search_result.get(request.user.username, [])
                
                if select_across == "0" and selected:
                    int_selected = [int(i) for i in selected.split(",")]
                    queryset = [i for i in queryset if int(i.id) in int_selected]
                
                mymodels_qs = MyQuerySet(model=self.model)
                mymodels_qs._result_cache = queryset
                return mymodels_qs
            
            raise Exception("action not found")


class BaseAdmin(admin.ModelAdmin):
    """基础管理类"""
    @display(description=mark_safe('<input type="checkbox" id="action-toggle">'))
    def action_checkbox(self, obj):
        try:
            return helpers.checkbox.render("_selected_action", str(obj.id))
        except:
            return helpers.checkbox.render("_selected_action", str(obj.pk))
    
    def get_search_results(self, request, queryset, search_term):
        try:
            LogEntry.objects.create(
                action_time=datetime.datetime.now(),
                user_id=request.user.id,
                action_flag=4,
                content_type_id=ContentType.objects.get(model=self.model.__name__).id
            )
        except:
            pass
        return super().get_search_results(request, queryset, search_term)
    
    def get_list_filter(self, request):
        original_list_filters = super().get_list_filter(request)
        new_list_filters = []
        
        for filter_name in original_list_filters:
            if isinstance(filter_name, str):
                field = self.model._meta.get_field(filter_name)
                if isinstance(field, models.CharField) and MultiSelectDropdownFilter:
                    new_list_filters.append((filter_name, MultiSelectDropdownFilter))
                else:
                    new_list_filters.append(filter_name)
            else:
                new_list_filters.append(filter_name)
        
        return new_list_filters


if AjaxAdmin:
    class BaseAjaxAdmin(AjaxAdmin):
        """基础 Ajax 管理类"""
        def get_search_results(self, request, queryset, search_term):
            try:
                LogEntry.objects.create(
                    action_time=datetime.datetime.now(),
                    user_id=request.user.id,
                    action_flag=4,
                    content_type_id=ContentType.objects.get(model=self.model.__name__).id
                )
            except:
                pass
            return super().get_search_results(request, queryset, search_term)
        
        def get_list_filter(self, request):
            original_list_filters = super().get_list_filter(request)
            new_list_filters = []
            
            for filter_name in original_list_filters:
                if isinstance(filter_name, str):
                    field = self.model._meta.get_field(filter_name)
                    if isinstance(field, models.CharField) and MultiSelectDropdownFilter:
                        new_list_filters.append((filter_name, MultiSelectDropdownFilter))
                    else:
                        new_list_filters.append(filter_name)
                else:
                    new_list_filters.append(filter_name)
            
            return new_list_filters


class YYDMAdmin(BaseAdmin):
    """影刀刀模后台"""
    using = 'yy_dm'
    
    def save_model(self, request, obj, form, change):
        obj.save(using=self.using)
    
    def delete_model(self, request, obj):
        obj.delete(using=self.using)
    
    def get_queryset(self, request):
        return super().get_queryset(request).using(self.using)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)
