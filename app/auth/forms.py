"""身份验证蓝本下的表单"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.models import User


class LoginForm(FlaskForm):
    # 用户登录表单
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    # 用户注册表单
    email = StringField('Email', validators=[DataRequired(),
                                             Length(1, 64),
                                             Email()])
    # 通过Regexp验证，保证username是以字母为开头，而且只包含字母，数字，下划线和点号。0代表为正则表达式，后面的为验证失败的消息
    username = StringField(
        'Username', validators=[
            DataRequired(), Length(
                1, 64), Regexp(
                '^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Username must have only letters, numbers,'
                'dots or underscores')])
    # 通过EqualTo验证，使两次密码必须相同，如果不相同则报错Password must match
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            EqualTo(
                'password2',
                message='Password must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        # 验证邮箱是否唯一
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        # 验证用户名是否唯一
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already registered')


class ChangePasswordForm(FlaskForm):
    # 修改密码表单
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('password2', message='Passwords must match')
    ])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(FlaskForm):
    # 申请重新设置密码表单
    email = StringField('Email', validators=[
        DataRequired(),
        Length(1, 64),
        Email()
    ])
    submit = SubmitField('Reset Password')


class PasswordResetForm(FlaskForm):
    # 重新设置密码表单
    password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('password2', message='Password must match')
    ])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


class ChangeEmailForm(FlaskForm):
    # 修改邮件地址表单
    email = StringField('New Email',validators=[
        DataRequired(),
        Length(1,64),
        Email()
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        # 检测修改邮件地址是否已经在使用中
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered')