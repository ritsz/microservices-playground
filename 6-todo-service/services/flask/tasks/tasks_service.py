from re import U
from flask import Flask, abort, request, make_response, jsonify
from pymongo import MongoClient
import json
import uuid


DATABASE_NAME = 'tasks_collection'
app = Flask(__name__)


def get_mongodb(name):
    client = MongoClient('mongodb', 27017, username='root', password='example')
    db = client.tasks_db
    login_col = db[name]
    return login_col


def close_mongodb():
    # Nothing to close.
    pass


class Task():
    def __init__(self, task_id, user_name, desc, status=False):
        self.task_id = task_id
        self.user_name = user_name
        self.desc = desc
        self.status = status
    
    @staticmethod
    def get_by_id(task_id):
        col = get_mongodb(name=DATABASE_NAME)
        task = col.find_one({'task_id': task_id})
        if not task:
            return None
        
        app.logger.info("Got Task %s", task)
        task = Task(
            task_id=task.get('task_id', str()),
            user_name=task.get('user', str()),
            desc=task.get('desc', str()),
            status=task.get('status', False)
        )
        return task

    @staticmethod
    def get_by_user_name_and_task_desc(user_name, task_desc):
        col = get_mongodb(name=DATABASE_NAME)
        task = col.find_one({'user': user_name, 'desc': task_desc})
        if not task:
            return None
        
        app.logger.info("Got Task %s", task)
        task = Task(
            task_id=task.get('task_id', str()),
            user_name=task.get('user', str()),
            desc=task.get('desc', str()),
            status=task.get('status', False)
        )
        return task

    @staticmethod
    def get_all_tasks_by_user_name(user_name):
        col = get_mongodb(name=DATABASE_NAME)
        tasks = col.find({'user': user_name})
        if not tasks:
            return None
        
        task_list = list()
        for task in tasks:
            app.logger.info("Got Task %s", task)
            task = {
                'task_id': task.get('task_id', str()),
                'user_name': task.get('user', str()),
                'desc': task.get('desc', str()),
                'status': task.get('status', False)
            }
            task_list.append(task)
        return task_list

    @staticmethod
    def get_all_tasks():
        col = get_mongodb(name=DATABASE_NAME)
        tasks = col.find({})
        if not tasks:
            return None
        
        task_list = list()
        for task in tasks:
            app.logger.info("Got Task %s", task)
            task = {
                'task_id': task.get('task_id', str()),
                'user_name': task.get('user', str()),
                'desc': task.get('desc', str()),
                'status': task.get('status', False)
            }
            task_list.append(task)
        return task_list
    
    @staticmethod
    def create(user_name, task_desc):
        task = Task.get_by_user_name_and_task_desc(user_name, task_desc)
        if task:
            return True, task.task_id

        task_id = str(uuid.uuid4())
        document = {
            'task_id': task_id,
            'user': user_name,
            'desc': task_desc,
            'status': False
        }
        app.logger.info('Adding %s to database', document)
        col = get_mongodb(name=DATABASE_NAME)
        return col.insert_one(document).acknowledged, task_id

    @staticmethod
    def delete_all_task(user_name):
        document = {
            'user': user_name
        }
        app.logger.info('Deleting all tasks for user %s', user_name)
        col = get_mongodb(name=DATABASE_NAME)
        return col.delete_many(document).deleted_count
    
    @staticmethod
    def update_all_tasks(user_name):
        document_filter = {
            'user': user_name
        }
        document_update = {
            'status': True
        }
        app.logger.info('Completing all tasks for user %s', user_name)
        col = get_mongodb(name=DATABASE_NAME)
        return col.update_many(document_filter, {'$set': document_update}).modified_count


@app.route('/tasks', methods=['GET'])
def get_all_tasks_for_user():
    user_name = request.args.get('user')
    if user_name:
        app.logger.info('Get all tasks for user %s', user_name)
        all_tasks = Task.get_all_tasks_by_user_name(user_name)
        app.logger.info("Tasks %s", all_tasks)
        return make_response(
                json.dumps(all_tasks),
                200,
            )
    else:
        app.logger.info('Get all tasks.')
        all_tasks = Task.get_all_tasks()
        app.logger.info("Tasks %s", all_tasks)
        return make_response(
                json.dumps(all_tasks),
                200,
            )


@app.route('/tasks', methods=['POST'])
def add_task_for_user():
    request_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    user_name = request_dict.get('user')
    desc = request_dict.get('desc')
    if not user_name or not desc:
        abort(400)
    ack, task_id = Task.create(user_name=user_name, task_desc=desc)
    return make_response(
                jsonify(
                    {"inserted": ack, "task_id": task_id}
                ),
                200,
            )


@app.route('/tasks', methods=['DELETE'])
def delete_tasks_for_user():
    user_name = request.args.get('user')
    if not user_name:
        abort(400)
    count = Task.delete_all_task(user_name=user_name)
    return make_response(
                jsonify(
                    {"deleted": count}
                ),
                200,
            )


@app.route('/tasks/complete', methods=['POST'])
def mark_task_complete():
    user_name = request.args.get('user')
    if not user_name:
        abort(400)
    count = Task.update_all_tasks(user_name=user_name)
    return make_response(
            jsonify(
                {"updated": count}
            ),
            200,
        )
      

@app.route('/')
def index():
    app.logger.info('Main Page')
    return "Welcome to Tasks Service."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)
    app.logger.info("Task Service has started")