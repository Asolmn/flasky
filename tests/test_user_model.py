import unittest
from app.models import User
import time
from app import create_app,db

class UserModelTestCase(unittest.TestCase):
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

    def test_password_setter(self):
        # 测试密码散列值是否为None
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        # 测试读取password属性时，抛出（找不到对应对象）异常
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        # 测试不同密码的散列值是否不同
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        # 测试相同密码的散列值是否相同
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        # 测试令牌是否能被正常还原
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))


    def test_invalid_confirmation_token(self):
        # 测试令牌的唯一性
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))


    def test_expired_confirmation_token(self):
        # 测试令牌的过期时间
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        # 使用测试令牌过期时间专用函数，生产环境中的令牌过期时间为一个小时
        token = u.generate_confirmation_token_test()
        time.sleep(2)
        self.assertFalse(u.confirm(token))
