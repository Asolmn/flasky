"""主脚本"""
import os
from app import create_app, db
from app.models import User, Role, Permission, Post, Follow
from flask_migrate import Migrate


app = create_app(os.environ.get('FLASK_CONFIG') or 'default')  # 使用默认环境
migrate = Migrate(app, db)


# 配置shell上下文
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission, Post=Post, Follow=Follow)


# 设置一个启动测试的命令
@app.cli.command()
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    app.run()
    app.debug(True)
