"""身份验证蓝本下的应用路由"""
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth
from app.models import User
from app.auth.form import LoginForm, RegistrationForm
from app import db
from app.email import send_email


# before_request()与unconfirmed() 允许未确认的用户登录，但是进一步获取访问权限时，必须先确认账号
# 满足两个函数中的条件，则before_app_request会拦截请求
@auth.before_app_request # before_app_request针对应用全局请求的钩子
def before_request():
    # 在请求开始之前，执行此函数，判断用户是否登录凭据有校，未确认账号，处理请求不是身份验证蓝图，处理请求的端点不为static特殊添加的路由
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed')) # 如果满足以上条件，重定向到unconfirmed()函数

@auth.route('/unconfirmed')
def unconfirmed():
    # 配合before_request()一起使用，为未确认账号进一步访问前的路由
    if current_user.is_anonymous or current_user.confirmed:  # 判断用户是否为匿名用户，账号是否已经确认
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 用户登录函数
    form = LoginForm()  # 获取登录表单
    if form.validate_on_submit():  # 如果表单中的数据通过验证提交
        user = User.query.filter_by(
            email=form.email.data).first()  # 通过表单中email的数据，查询对应的用户
        if user is not None and user.verify_password(
                form.password.data):  # 如果用户不为空，且通过密码验证，则允许登录
            login_user(user, form.remember_me.data)  # 通过login_user在用户会话中标记已登录
            # flask-login会把原URL保存到next参数中，可以通过request.args字典查询
            next = request.args.get('next')
            if next is None or not next.startswith(
                    '/'):  # 如果查询字符串中没有next，且通过验证，则重定向到首页
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required  # 保护路由，login_required装饰器可以只让通过认证的用户登录
def logout():
    # 用户登出函数
    logout_user()
    flash('You have been logged out') # 弹出提示
    return redirect(url_for('main.index')) # 重定向回首页


@auth.route('/register', methods=['GET', 'POST'])
def register():
    # 用户注册函数
    form = RegistrationForm()
    if form.validate_on_submit():
        # 根据表单数据创建一个新用户
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
        )
        # 提交数据库会话
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        # 发送邮件 send_email(收件人，主题，模板位置，可变参数)
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email')
        # 重定向到登录页面
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required # 保护路由，只有点击链接后，先登录才可以执行此函数
def confirm(token):
    # 确认用户函数
    if current_user.comfired: # 以访问的用户中是否已确认
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit() # 传入token，标记用户为已确认
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    # 重新发送用户确认邮件函数
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email')
    return redirect(url_for('main.index'))