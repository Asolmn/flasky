"""数据库模型"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from app import db


@login_manager.user_loader
def load_user(user_id):
    # 加载用户，在扩展需要从数据库中获取指定标识符对应用户时调用
    # 需要获取已登录用户的信息时调用
    return User.query.get(int(user_id))


class Role(db.Model):
    # 用户角色模型
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 寻找关系中的外键，同时向User类中添加一个role属性
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    # 用户模型
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # 添加一个外键，与roles表中的id行建立关系
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self, expiration=3600):
        # 生成一个令牌，有效期为1一个小时
        s = Serializer(
            current_app.config['SECRET_KEY'],
            expiration)  # 以SECRET_KEY为密钥
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def generate_confirmation_token_test(self, expiration=1):
        # 为单元测试使用令牌过期时间的函数，有效期为1s
        s = Serializer(
            current_app.config['SECRET_KEY'],
            expiration)  # 以SECRET_KEY为密钥
        return s.dumps({'confirm': self.id}).decode('utf-8')


    def generate_reset_token(self, expiration=3600):
        # 生成重置密码用的令牌
        s = Serializer(
            current_app.config['SECRET_KEY'],
            expiration
        )
        return s.dumps({'reset':self.id}).decode('utf-8') # 以需要重置密码的用户id作为令牌加密数据

    @staticmethod
    def reset_password(token, new_password):
        # 验证令牌和重置密码
        s = Serializer(current_app.config['SECRET_KEY']) # 设置密钥s
        try:
            data = s.loads(token.encode('utf-8')) # 通过生成的令牌还原数据
        except:
            return False
        user =User.query.get(data.get('reset')) # 查询对应id的用户
        if user is None:
            return False
        user.password = new_password # 修改密码
        db.session.add(user) # 添加到数据库会话中，等待提交
        return True

    def confirm(self, token):
        # 确认令牌
        s = Serializer(current_app.config['SECRET_KEY'])  # 生成密钥
        try:
            data = s.loads(token.encode('utf-8'))  # 通过密钥还原数据
        except:
            return False
        if data.get('confirm') != self.id:  # 检验用户id是否等于登录中的用户匹配
            return False
        self.confirmed = True  # 确认令牌后，将confirmed字段设置为True
        db.session.add(self)  # 直接add(self)，可以直接新增的内容加入数据库
        return True


    # 设置名为password只读属性，和@*.setter搭配使用
    @property
    def password(self):
        raise AttributeError('password is not readable attribute')

    # 通过setter和property搭配，当password_hash写入后，不可再读取password属性的值
    @password.setter
    def password(self, password):
        # 计算密码散列值
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        # 对比密码散列值
        return check_password_hash(self.password_hash, password)


    def __repr__(self):
        return '<User %r>' % self.username
