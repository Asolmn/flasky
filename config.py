"""配置文件"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """配置参数类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asolmn'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = os.environ.get('MAIL_PORT', '587')
    # 如果变量MAIL_USE_TLS在[true,on,1]中则返回True，没有设定默认为true，使用lower()转为大写
    MAIL_USE_TLS = os.environ.get(
        'MAIL_USE_TLS', 'False').lower() in [
        'true', 'on', '1']  # 使用googlemail.com，则设置为True
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() in [
        'true', 'on', '1']  # 使用googlemail.com这一条要关掉
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = os.environ.get(
        'FLASKY_MAIL_SENDER', 'asolmn0707@gmail.com')
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASKY_POSTS_PER_PAGE = 10


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发环境"""
    DEBUG = True
    # 测试环境中使用内存中的数据库，测试运行后无需保留任何数据，所以不用数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    """测试环境"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):
    """生产环境"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


# 设置默认环境
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
