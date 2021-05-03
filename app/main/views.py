"""主蓝本中的应用路由"""
from flask import render_template, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from app.main import main
from app.models import User, Role
from app.main.forms import EditfileForm, EditProfileAdminForm
from app import db
from app.decorators import admin_required

@main.route('/', methods=['GET', 'POST'])
def index():
    # 主页
    return render_template('index.html')

@main.route('/user/<username>')
def user(username):
    # 用户资料页面
    user = User.query.filter_by(username=username).first_or_404() # 查询相应的用户名，如果搜索不到返回404错误
    return render_template('user.html', user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # 编写用户资料函数
    form = EditfileForm()
    if form.validate_on_submit():
        # 获取表单中的数据，并赋值给当前登录用户对应的属性
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        # 因为current_user处于一个单独的线程，如果使用current_app则永远获取不到对象，没有flask上下文，所以要用_get_current_object()
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated')
        # 跳转到用户资料页面
        return redirect(url_for('main.user',username=current_user.username))
    # 重置表单数据
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    # 管理员编写资料函数
    user = User.query.get_or_404(id) # 查询对应用户id的用户
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        # 分别将表单对应属性的数据赋值给用户
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        # 提交到数据库
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated')
        # 跳转到用户资料页面
        return redirect(url_for('main.user', username=user.username))
    # 将用户对应属性的数据，分别重新放到表单对应属性中
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)