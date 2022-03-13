from flask import Flask, abort, request, make_response, jsonify
from flask_prometheus_metrics import register_metrics
from prometheus_client import make_wsgi_app
from pymongo import MongoClient
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import json
import requests
import uuid


DATABASE_NAME = 'user_collection'
app = Flask(__name__)


def get_mongodb(name):
    client = MongoClient('mongodb', 27017, username='root', password='example')
    db = client.users_db
    login_col = db[name]
    return login_col


def close_mongodb():
    # Nothing to close.
    pass


class User():
    def __init__(self, id, name, task_list=None):
        self.id = id
        self.name = name
        self.task_list = list() if task_list==None else task_list

    @staticmethod
    def get_by_name(user_name):
        col = get_mongodb(name=DATABASE_NAME)
        user = col.find_one({'user_name': user_name})
        if not user:
            return None

        app.logger.info("Got user %s", user)

        user = User(
            id=user.get('user_id', str()),
            name=user.get('user_name', str()),
            task_list=user.get('task_list', list())
        )
        return user

    @staticmethod
    def create(user_name):
        user = User.get_by_name(user_name)
        if user:
            return True, user.id

        user_id = str(uuid.uuid4())
        document = {
            'user_id': user_id,
            'user_name': user_name,
            'task_list': list()
        }
        app.logger.info('Adding %s to database', document)
        col = get_mongodb(name=DATABASE_NAME)
        return col.insert_one(document).acknowledged, user_id

    @staticmethod
    def update_task_list(user_name, task_id):
        user = User.get_by_name(user_name)
        if not user:
            return None
        tasks = user.task_list
        tasks.append(task_id)

        document_filter = {
            'user_name': user_name
        }
        document_update = {
            'task_list': tasks
        }
        app.logger.info("Updating task list for %s", user_name)
        col = get_mongodb(name=DATABASE_NAME)
        return col.update_one(document_filter, {'$set': document_update}).modified_count

    @staticmethod
    def delete(user_name):
        user = User.get_by_name(user_name)
        if not user:
            app.logger.info("Didn't delete because could not find %s", user_name)
            return None

        document = {
            'user_name': user_name
        }
        app.logger.info('Deleting %s from database', document)
        col = get_mongodb(name=DATABASE_NAME)
        return col.delete_one(document).acknowledged


@app.route('/users/<name>', methods=['GET'])
def get_user(name):
    app.logger.info('Getting user %s', name)
    user = User.get_by_name(name)
    if not user:
        return abort(404)
    return make_response(
                jsonify(
                    {"user_name": user.name},
                    {"user_id": user.id},
                    {"tasks-service": user.task_list}
                ),
                200,
            )

@app.route('/users/<name>', methods=['POST'])
def add_user(name):
    app.logger.info('Adding user %s', name)
    ack, user_id = User.create(name)
    if not ack:
        abort(409)
    return make_response(
                jsonify(
                    {"inserted": ack, "user_id": user_id}
                ),
                200,
            )


@app.route('/users/<name>/task', methods=['POST'])
def add_user_task(name):
    request_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    desc = request_dict.get('desc')
    if not desc:
        abort(400)
    task = {
        'user': name,
        'desc': desc
    }
    response = requests.post('http://tasks-service:6000/tasks', json=task)
    task_id = response.json().get('task_id')
    app.logger.info("Added task %s", task_id)
    count = User.update_task_list(user_name=name, task_id=task_id)
    if not count:
        abort(400)
    return make_response(
            jsonify(
                {"added": count}
            ),
            200,
        )


@app.route('/users/<name>', methods=['DELETE'])
def delete_user(name):
    user = User.get_by_name(name)
    if not user:
        return abort(404)

    response = requests.delete('http://tasks-service:6000/tasks?user={}'.format(name)).json().get("deleted")
    app.logger.info("Deleted %s tasks-service.", response)
    if len(user.task_list) != response:
        app.logger.error("Mismatch between 2 services")
    app.logger.info('Deleting user %s', name)
    deleted = User.delete(name)
    return make_response(
            jsonify(
                {"deleted": deleted}
            ),
            200,
        )


if __name__ == '__main__':
    # provide app's version and deploy environment/config name to set a gauge metric
    register_metrics(app, app_version="v0.1.2", app_config="staging")

    # Plug metrics WSGI app to your main app with dispatcher
    dispatcher = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

    run_simple(hostname="0.0.0.0", port=8080, application=dispatcher, use_debugger=True)
    app.logger.info("User Service has started")