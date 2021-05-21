"""数据库模型"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from app import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from app import db
from datetime import datetime
import hashlib
from datetime import datetime
from markdown import markdown
import bleach


class Permission:
    """
    各项用户的权限权重
    匿名：无
    普通用户： FOLLOW COMMENT WRITE
    协助管理员： FOLLOW COMMENT WRITE MODERATE
    管理员： FOLLOW COMMENT WRITE MODERATE ADMIN
    """
    FOLLOW = 1  # 关注用户
    COMMENT = 1  # 发表评论
    WRITE = 4  # 写文章
    MODERATE = 8  # 管理其它用户的评论
    ADMIN = 16  # 管理员权限


class Role(db.Model):
    # 用户角色模型
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True) # 角色名
    default = db.Column(db.Boolean, default=False, index=True)  # 默认角色
    permissions = db.Column(db.Integer)  # 权限字段
    # 寻找关系中的外键，同时向User类中添加一个role属性
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        # 未给构造函数提供参数之前，permissions为0
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        # 添加权限
        if not self.has_permission(perm):  # 判断权限是否已经存在
            self.permissions += perm

    def remove_permission(self, perm):
        # 删除权限
        if self.has_permission(perm):  # 判断权限是否存在
            self.permissions -= perm

    def reset_permission(self):
        # 重置权限
        self.permissions = 0

    def has_permission(self, perm):
        # 判断是否已经有此权限
        # 使用位运算，如果有此权限，位运算之后，self.permission & perm和perm必然相等，则返回True，反之为False
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        # 用户角色字典
        roles = {
            'User': [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE],
            'Moderator': [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE],
            'Administrator': [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN]}
        default_role = 'User'  # 默认用户角色为User
        for r in roles:
            role = Role.query.filter_by(name=r).first()  # 依次查询角色列表中的角色
            if role is None:  # 如果角色不在Role表中，则进行创建
                role = Role(name=r)
            role.reset_permission()  # 对角色的权限进行重置
            for perm in roles[r]:  # 循环角色的权限列表
                role.add_permission(perm)  # 通过权限列表为角色添加权限
            # 如果用户角色为默认角色，则将default字段设置为True
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Post(db.Model):
    # 博客文章模型
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text) # 正文
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # 时间戳
    author_id = db.Column(db.Integer, db.ForeignKey('users.id')) # 与users表中的id进行关联
    body_html = db.Column(db.Text) # 博客正文的html代码

    @staticmethod
    def on_change_body(target, value, oldvalue, initiator):
        # 处理Markdown文本
        # 允许的html标签
        allowed_tags = [
            'a','abbr','acronym','b','blockquote','code','em','i',
            'li','ol','pre','strong','ul','h1','h2','h3','p'
        ]
        # markdown()将markdown文本转换为html格式, 传给bleach的clean函数进行筛选
        # linkify为文本中的url自动添加<a>链接，Markdown规范中并没有这一功能，但是PageDown扩展实现了这个功能，所以服务端也要保持一直
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'),
                tags = allowed_tags,
                strip = True,
            )
        )

# 监听Post的body字段，如果发生更新，on_change_body自动调用，渲染成html格式
db.event.listen(Post.body, 'set', Post.on_change_body)


class Follow(db.Model):
    # 用户关注之间的关联表
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True) # 关注者
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True) # 被关注者
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # 关注时间


class User(UserMixin, db.Model):
    # 用户模型
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True) # 邮箱
    username = db.Column(db.String(64), unique=True, index=True) # 用户名
    # 添加一个外键，与roles表中的id行建立关系
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128)) # 密码散列值
    confirmed = db.Column(db.Boolean, default=False) # 确认账号字段
    # 用户资料字段
    name = db.Column(db.String(64)) # 真实姓名
    location = db.Column(db.String(64)) # 所在地
    about_me = db.Column(db.Text()) # 关于自己
    member_since = db.Column(db.DateTime(), default=datetime.utcnow) # 注册日期 utcnow无需加()，因为default可以接受函数作为默认值
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow) # 最后一次访问日期
    avatar_hash = db.Column(db.String(32)) # 头像url
    posts = db.relationship('Post', backref='author', lazy='dynamic') # 自动寻找User和Post的外键关系，向Post中添加author属性
    # 关注用户外键, 表明此用户关注了多少用户
    followed = db.relationship(
        'Follow',
        foreign_keys=[Follow.follower_id],
        backref=db.backref('follower', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    # 被关注用户外键， 表明此用户被多少用户关注
    followers = db.relationship(
        'Follow',
        foreign_keys=[Follow.followed_id],
        backref=db.backref('followed', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)  # 调用User父类的__init__
        if self.role is None:  # 如果用户角色为None
            # 如果用户的邮箱与管理员邮箱一致
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(
                    name='Administrator').first()  # 将用户角色修改为管理员角色
            if self.role is None:
                self.role = Role.query.filter_by(
                    default=True).first()  # 如果非与管理员邮箱不一致，统一设置为默认角色
        if self.email is not None and self.avatar_hash is None:
            # 如果邮箱地址存在，且头像url不存在
            self.avatar_hash = self.gravatar_hash() # 生成邮件地址对应的散列值

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
        return s.dumps({'reset': self.id}).decode(
            'utf-8')  # 以需要重置密码的用户id作为令牌加密数据

    def generate_email_change_token(self, new_email, expiration=3600):
        # 生成重置邮件地址用的令牌
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({
            'change_email_user_id': self.id,
            'new_email': new_email}).decode('utf-8')  # 以新邮件地址和用户id作为令牌加密数据

    def change_email(self, token):
        # 修改邮件地址
        s = Serializer(current_app.config['SECRET_KEY'])  # 生成密钥
        try:
            data = s.loads(token.encode('utf-8'))  # 还原数据
        except BaseException:
            return False
        if data.get(
                'change_email_user_id') != self.id:  # 申请修改邮件地址的用户id与登录用户id是否匹配
            return False
        new_email = data.get('new_email')
        if new_email is None:  # 判断新邮件地址是否为空
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            # 查询新邮件地址是否与旧邮件地址相同
            return False
        self.email = new_email  # 修改密码
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)  # 将用户修改添加到数据库会话中
        return True

    @staticmethod
    def reset_password(token, new_password):
        # 验证令牌和重置密码
        s = Serializer(current_app.config['SECRET_KEY'])  # 设置密钥s
        try:
            data = s.loads(token.encode('utf-8'))  # 通过生成的令牌还原数据
        except BaseException:
            return False
        user = User.query.get(data.get('reset'))  # 查询对应id的用户
        if user is None:
            return False
        user.password = new_password  # 修改密码
        db.session.add(user)  # 添加到数据库会话中，等待提交
        return True

    def confirm(self, token):
        # 确认令牌
        s = Serializer(current_app.config['SECRET_KEY'])  # 生成密钥
        try:
            data = s.loads(token.encode('utf-8'))  # 通过密钥还原数据
        except BaseException:
            return False
        if data.get('confirm') != self.id:  # 检验用户id是否等于登录中的用户匹配
            return False
        self.confirmed = True  # 确认令牌后，将confirmed字段设置为True
        db.session.add(self)  # 因为self指的是引用对象的实例，所以add(self),相当于添加这个用户
        return True

    @property  # 设置名为password只读属性，和@*.setter搭配使用
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

    def can(self, perm):
        # 判断用户角色权限与是否存在
        return self.role is not None and self.role.has_permission(perm)  # 角色存在同时是管理员权限返回True

    def is_administrator(self):
        # 判断用户是否为管理员账号
        return self.can(Permission.ADMIN)

    def ping(self):
        # 每次访问网站后，刷新用户的最后访问时间
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def gravatar_hash(self):
        # 生成邮件地址对应的md5散列值
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        # 生成头像服务所使用的Gravatar URL
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar/'
        else:
            url = 'https://gravatar.zeruns.tech/avatar/'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        # 关注方法
        # 如果user没有关注当前用户，则Follow中插入一条关注记录
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        # 取消关注方法
        # 从此用户关注的用户中，找到被关注是user的Follow对象
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            # 删除这条关注记录
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        # 当前此用户关注的用户中，如果存在被关注者是user，证明关注关系存在，返回True，反之为False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        # 当前关注此用户的用户中，如果存在关注者等于user，证明关注关系存在，返回True，反之为False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    # 匿名用户权限检查
    def can(self, permissions):
        # 因为匿名用户没有权限，所以直接false
        return False

    def is_administrator(self):
        # 与can同理
        return False


@login_manager.user_loader
def load_user(user_id):
    # 加载用户，在扩展需要从数据库中获取指定标识符对应用户时调用
    # 需要获取已登录用户的信息时调用
    return User.query.get(int(user_id))


login_manager.anonymous_user = AnonymousUser  # 告诉Flask-login使用自定义的匿名用户类
