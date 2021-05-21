"""主蓝本中的应用路由"""
from flask import render_template, abort, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.main import main
from app.models import User, Role, Permission, Post
from app.main.forms import EditfileForm, EditProfileAdminForm, PostForm
from app import db
from app.decorators import admin_required


@main.route('/', methods=['GET', 'POST'])
def index():
    # 主页
    form = PostForm()
    # 如果当前登录用户具有写权限同时表单验证通过
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        # 因为current_user是一个代理对象，本质上是一个包装好的用户对象，sqlalchemy不能接受代理对象，所以要用_get_current_object()去访问
        # 内部的用户对象，与Post(body=form.body.data, user_id=current.id)等效
        post = Post(
            body=form.body.data,
            author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))  # 重定向到主页
    # posts = Post.query.order_by(Post.timestamp.desc()).all() # 查询所有文章，以最新时间进行排序, desc()降序
    # 分页显示博客文章列表
    page = request.args.get('page', 1, type=int) # 获取渲染页数，默认渲染第一页
    pagination = Post.query.order_by(
        Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items # item属性表示当前页面的记录
    return render_template(
        'index.html',
        form=form,
        posts=posts,
        pagination=pagination)


@main.route('/user/<username>')
def user(username):
    # 用户资料页面
    user = User.query.filter_by(
        username=username).first_or_404()  # 查询相应的用户名，如果搜索不到返回404错误
    # posts = user.posts.order_by(Post.timestamp.desc()).all()  # 获取查询用户的所有文章
    page = request.args.get('page', 1, type=int) # 获取渲染页数，默认渲染第一页
    pagination = Post.query.order_by(
        Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items # item属性表示当前页面的记录
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


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
        return redirect(url_for('main.user', username=current_user.username))
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
    user = User.query.get_or_404(id)  # 查询对应用户id的用户
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


@main.route('/post/<int:id>')
def post(id):
    # 文章固定链接
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])

@main.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    # 编辑博客文章
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        # 只允许作者本身和管理编辑，否则就403
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        # 提交数据
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@main.route('/remove_post/<int:id>')
def remove_post(id):
    # 删除文章
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('main.index'))
