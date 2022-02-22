from enum import Enum
from flask_login import UserMixin

from db import get_mongodb


class Permissions(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, password='', permissions=Permissions.NONE):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.password = password
        self.permissions = permissions

    @staticmethod
    def get(user_id):
        login_col = get_mongodb()
        user = login_col.find_one({"user_id": user_id})

        if not user:
            return None

        user = User(
            id_=user.get('user_id', None),
            name=user.get('name', None),
            email=user.get('email', None),
            profile_pic=user.get('profile_pic', None),
            password=user.get('password', None),
            permissions=str(user.get('permissions', None))
        )
        return user

    @staticmethod
    def get_by_name(name):
        login_col = get_mongodb()
        user = login_col.find_one({"name": name})

        if not user:
            return None

        user = User(
            id_=user.get('user_id', None),
            name=user.get('name', None),
            email=user.get('email', None),
            profile_pic=user.get('profile_pic', None),
            password=user.get('password', None),
            permissions=str(user.get('permissions', None))
        )
        return user

    @staticmethod
    def create(id_, name, email='', profile_pic='', password='', permissions=Permissions.WRITE):
        user = get_by_name(name)
        if user:
            return None
        document = {
            'user_id': id_,
            'name': name,
            'email': email,
            'profile_pic': profile_pic,
            'password': password,
            'permissions': str(permissions)
        }
        login_col = get_mongodb()
        insert_id = login_col.insert_one(document).inserted_id
        return insert_id
