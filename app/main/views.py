"""主蓝本中的应用路由"""
from flask import render_template, abort, flash, redirect, url_for, request, current_app, make_response
from flask_login import login_required, current_user
from app.main import main
from app.models import User, Role, Permission, Post
from app.main.forms import EditfileForm, EditProfileAdminForm, PostForm
from app import db
from app.decorators import admin_required, permission_required


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
    show_followed = False # 用于判断只显示所关注用户的文章，还是全部文章
    if current_user.is_authenticated:
        # show_followed存储在cookies中，如果其值为非空字符串，表示只显示所关注用户的文章，反之则相反
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        # 根据show_followed其值的不同，设置不同的查询对象
        query = current_user.followed_posts # 调用封装好的方法，另查询对象等于所关注用户的文章
    else:
        query = Post.query
    # 分页显示博客文章列表
    page = request.args.get('page', 1, type=int)  # 获取渲染页数，默认渲染第一页
    pagination = query.order_by(
        Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items  # item属性表示当前页面的记录
    return render_template(
        'index.html',
        form=form,
        posts=posts,
        pagination=pagination,
        show_followed=show_followed)


@main.route('/user/<username>')
def user(username):
    # 用户资料页面
    user = User.query.filter_by(
        username=username).first_or_404()  # 查询相应的用户名，如果搜索不到返回404错误
    # posts = user.posts.order_by(Post.timestamp.desc()).all()  # 获取查询用户的所有文章
    query = Post.query.filter_by(author=user) # 获取user的博客文章
    page = request.args.get('page', 1, type=int)  # 获取渲染页数，默认渲染第一页
    pagination = query.order_by(
        Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items  # item属性表示当前页面的记录
    return render_template(
        'user.html',
        user=user,
        posts=posts,
        pagination=pagination)


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


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    # 关注用户
    user = User.query.filter_by(username=username).first()  # 查找与username对应的用户
    if user is None:  # 如果用户不存在
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):  # 判断当前用户是否已经关注了user
        flash('You are already following this user')
    current_user.follow(user)  # 调用封装好的关注用户方法
    db.session.commit()  # 提交到数据库
    flash('You are now following %s' % username)
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    # 取消关注
    user = User.query.filter_by(username=username).first()  # 查找与username对应的用户
    if user is None:  # 如果用户不存在
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):  # 如果user还未关注当前用户
        flash('You have not followed this user')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)  # 调用封装好的取消关注方法
    db.session.commit()
    flash('Success unfollow')
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    # 显示关注此用户的用户列表
    user = User.query.filter_by(username=username).first() # 查询用户名对应的用户
    if user is None:
        flash('Invalid user')
        return redirect(url_for('main.index'))
    # 对用户列表进行分页
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page,
        per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    # 获取当前页的用户列表
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template(
        'followers.html',
        user=user,
        title='Followers of',
        endpoint='main.followers',
        pagination=pagination,
        follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    # 显示当前用户关注的用户的列表
    user = User.query.filter_by(username=username).first() # 查询对应的用户
    if user is None:
        flash('Invalid user')
        return redirect(url_for('main.index'))
    # 对用户列表进行分页
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page,
        per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    # 获取当前页的用户列表，并存入字典
    follows =[{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template(
        'followers.html',
        user=user,
        title='Followed of',
        endpoint='main.followed_by',
        pagination=pagination,
        follows=follows
    )


@main.route('/all')
@login_required
def show_all():
    # 设置查询所有文章的show_followed的cookie值
    resp = make_response(redirect(url_for('main.index'))) # cookie只能在响应对象中设置，所以不能依赖Flask，通过make_response创建响应
    # 设置cookie的名称和值，以及过期时间，这里的过期时间为30天
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    # 设置查询只关注用户的show_followed的cookie值
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp