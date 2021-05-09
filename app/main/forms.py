"""主蓝本中的表单"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, ValidationError, FileField
from wtforms.validators import DataRequired, Length, Email, Regexp
from app.models import Role, User


class EditfileForm(FlaskForm):
    # 用户资料编辑表单
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    # 管理员用户资料编辑表单
    email = StringField('Email', validators=[
        DataRequired(),
        Length(1, 64),
        Email()
    ])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$',
               0,
               'Usernames must have only letters, numbers, dots or underscores')
    ])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int) # coerce=int标识符字段的值转换为整数
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        # SelectFiled为下拉菜单实例，必须设置choices属性，由一个元组构成，包含两个元素，选项的标识符，显示在控件中的文本文字
        # 以Role.name的字母顺序的所有角色，元组由角色的id和name构成
        self.role.choices = [
            (role.id, role.name) for role in Role.query.order_by(Role.name).all()
        ]
        # 传入用户
        self.user = user

    def validate_email(self, field):
        # 判断邮箱是否等于原本的邮箱，同时是否已经在数据库中存在
        if field.data != self.user.email and \
            User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        # 判断用户名是否等于原本的用户名，同时是否已经在数据库中存在
        if field.data != self.user.username and \
            User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use')


class PostForm(FlaskForm):
    pass