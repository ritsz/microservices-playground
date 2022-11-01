import json
from threading import Thread
from time import sleep

from flask import Flask, abort, make_response, jsonify
from flask_prometheus_metrics import register_metrics
from kafka import KafkaConsumer
from prometheus_client import make_wsgi_app
from pymongo import MongoClient
from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware


import os
import sys
import logging

DB_URL=os.getenv('MONGODB_URL', default='node-2')
DB_USER=os.getenv('MONGODB_USER', default='root')
DB_PASS=os.getenv('MONGODB_PASS', default='example')

app = Flask(__name__)

log_level = logging.INFO
 
for handler in app.logger.handlers:
    app.logger.removeHandler(handler)

root = os.path.dirname(os.path.abspath(__file__))
logdir = os.path.join(root, 'logs')
if not os.path.exists(logdir):
    os.mkdir(logdir)
log_file = os.path.join(logdir, 'app.log')
handler = logging.FileHandler(log_file)
handler.setLevel(log_level)
app.logger.addHandler(handler)

app.logger.setLevel(log_level)

DATABASE_NAME = 'file_collection'

def get_mongodb(name):
    client = MongoClient(DB_URL, 27017, username='root', password='example')
    db = client.users_db
    login_col = db[name]
    return login_col


def close_mongodb():
    # Nothing to close.
    pass


class File():
    def __init__(self, id, original_name, bucket_name, file_size, sha256, analysis_list=None):
        self.id = id
        self.original_name = original_name
        self.analyses = analysis_list
        self.bucket_name = bucket_name
        self.file_size = file_size
        self.sha256 = sha256

    @staticmethod
    def get_by_name(original_name):
        col = get_mongodb(name=DATABASE_NAME)
        file = col.find_one({'original_name': original_name})
        if not file:
            app.logger.info("Got NO file %s", original_name)
            return None

        app.logger.info("Got file %s", file)
        return file

    @staticmethod
    def get_by_id(id):
        col = get_mongodb(name=DATABASE_NAME)
        file = col.find_one({'id': id})
        if not file:
            app.logger.info("Got NO file %s", id)
            return None

        app.logger.info("Got file %s", file)
        return file

    @staticmethod
    def create(id, original_name, bucket_name, file_size, sha256, analysis_list=None):
        file = File.get_by_id(id)
        if file:
            return True, file

        document = {
            'id': id,
            'original_name': original_name,
            'bucket_name': bucket_name,
            'file_size': file_size,
            'sha256': sha256,
            'analyses': analysis_list
        }
        app.logger.info('Adding %s to database', document)
        col = get_mongodb(name=DATABASE_NAME)
        return col.insert_one(document).acknowledged, id

    @staticmethod
    def update_analyses_list(id, analysis):
        file = File.get_by_id(id)
        if not file:
            return None

        analyses = file.analyses
        analyses.append(analysis)

        document_filter = {
            'id': id
        }
        document_update = {
            'analyses': analyses
        }
        app.logger.info("Updating analyses %s for %s", analysis, file)
        col = get_mongodb(name=DATABASE_NAME)
        return col.update_one(document_filter, {'$set': document_update}).modified_count

    @staticmethod
    def delete(id):
        file = File.get_by_id(id)
        if not file:
            app.logger.info("Didn't delete because could not find %s", id)
            return None

        document = {
            'id': id
        }
        app.logger.info('Deleting %s from database', document)
        col = get_mongodb(name=DATABASE_NAME)
        return col.delete_one(document).acknowledged


@app.route('/api/v1/analysis/file/<id>', methods=['GET'])
def get_file_analysis(id):
    app.logger.info("Getting analysis of file %s", id)
    file = File.get_by_id(id)
    if not file:
        return abort(404)
    return make_response(
        jsonify(
            {"original_name": file['original_name']},
            {"id": file['id']},
            {"bucket_name": file['bucket_name']},
            {"file_size": file['file_size']},
            {"sha256": file['sha256']},
            {"analyses": file['analyses']}
        ),
        200,
    )


@app.route('/health')
def health():  # put application's code here
    return 'UP'


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


# long-running background task for consuming messages and updating File Documents.
def background_task():
    sleep(25)
    while True:
        app.logger.info("Waiting for a message")
        consumer = KafkaConsumer('postgres-database.public.file_entity', bootstrap_servers='kafka:9092')
        msg = next(consumer)
        file = json.loads(msg.value.decode())['payload']['after']
        ack, id = File.create(file['id'],
                              file['original_file_name'],
                              file['bucket_name'],
                              file['file_size'],
                              file['sha256'],
                              analysis_list=None)
        app.logger.info("File created %s : %s", ack, id)
        sleep(2)


daemon = Thread(target=background_task, name='MessageConsumer')
daemon.start()

if __name__ == '__main__':

    # provide app's version and deploy environment/config name to set a gauge metric
    register_metrics(app, app_version="v0.1.2", app_config="staging")

    # Plug metrics WSGI app to your main app with dispatcher
    dispatcher = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

    run_simple(hostname="0.0.0.0", port=9080, application=dispatcher, use_debugger=True)
    app.logger.info("User Service has started")
