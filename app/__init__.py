"""应用包的构造文件"""
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # 设置登录页面端点
pagedown = PageDown()

def create_app(config_name):
    app = Flask(__name__)
    # 通过from_object将配置对象导入
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 调用init_app将扩展对象初始化
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    pagedown.init_app(app)


    # 注册蓝本
    from .main import main as main_blueprint # 主蓝本
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint # 身份验证蓝本
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

