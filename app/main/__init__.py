"""主蓝本"""
from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission

@main.app_context_processor # 上下文处理器，可以将自定义变量在所有模板中全局访问
def inject_permissions():
    # 将Permission加入模板上下文
    return dict(Permission=Permission)