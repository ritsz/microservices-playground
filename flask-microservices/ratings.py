from flask import Flask, abort, request
import os
import socket
import json
import uuid

app = Flask(__name__)
rating_database = list()

@app.route('/ratings')
def get_ratings():
    film_name = request.args.get('name')
    if film_name:
        return get_rating(film_name)
    else:
        app.logger.info('{}: Getting all film ratings {}'.format(get_debug_string(), rating_database))
        return json.dumps(rating_database)


@app.route('/ratings/<id>', methods=['GET'])
def get_rating_by_id(id):
    app.logger.info('{}: Getting film rating {}'.format(get_debug_string(), id))
    for item in rating_database:
        if item['id'] == id:
            return json.dumps(item)
    abort(404)

@app.route('/ratings', methods=['POST'])
def post_rating():
    global rating_database
    film_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    # if film_dict.get('id', None) is None:
    #     film_dict['id'] = str(uuid.uuid4())
    rating_database.append(film_dict)
    app.logger.info('{}: Added film {}: {}'.format(get_debug_string(), id, film_dict))
    return json.dumps(rating_database)

def get_rating(film_name):
    app.logger.info('{}: Getting film {}'.format(get_debug_string(), film_name))
    for item in rating_database:
        if item['name'] == film_name:
            return json.dumps(item)
    abort(404)

def get_debug_string():
    return '(service {}):(hostname {})'.format(os.environ['SERVICE_NAME'], socket.gethostname())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)
    app.logger.info("Ratings Service has started")
