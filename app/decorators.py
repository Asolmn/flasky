"""检查用户权限的自定义装饰器，用于让视图函数对具有特定权限的用户开放"""
from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import Permission

def permission_required(permission):
    def decorator(f):
        @wraps(f) # 使用wraps保证装饰器 装饰后的函数还拥有原来的属性
        def decorator_function(*args, **kwargs):
            # 如果用户没有此权限，返回403响应
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorator_function # 返回内嵌函数的引用
    return decorator

def admin_required(f):
    # 验证管理员权限
    return permission_required(Permission.ADMIN)(f)