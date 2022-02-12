from pymongo import MongoClient


def get_mongodb(name='login_collection'):
    client = MongoClient('mongodb', 27017, username='root', password='example')
    db = client.login_db
    login_col = db[name]
    return login_col


def close_mongodb():
    pass

