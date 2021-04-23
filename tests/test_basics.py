"""单元测试"""
import unittest
from flask import current_app
from app import create_app, db


class BasicsTestCase(unittest.TestCase):
    # 创建一个测试环境，通过creat_all()创建一个全新的数据库
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    # 删除数据库和应用上下文
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 测试应用实例是否存在
    def test_app_exists(self):
        self.assertFalse(current_app is None)

    # 测试应用是否在测试配置中运行
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
