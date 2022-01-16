from flask import Flask, abort, request
import os
import socket
import json
import uuid

app = Flask(__name__)
film_database = list()

@app.route('/films')
def get_films():
    film_name = request.args.get('name')
    if film_name:
        return get_film(film_name)
    else:
        app.logger.info('{}: Getting all films {}'.format(get_debug_string(), film_database))
        return json.dumps(film_database)

@app.route('/films/<id>', methods=['GET'])
def get_film_by_id(id):
    app.logger.info('{}: Getting film {}'.format(get_debug_string(), id))
    for item in film_database:
        if item['id'] == id:
            return json.dumps(item)
    abort(404)

@app.route('/films', methods=['POST'])
def post_film():
    global film_database
    film_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    film_dict['id'] = str(uuid.uuid4())
    film_database.append(film_dict)
    app.logger.info('{}: Added film {}: {}'.format(get_debug_string(), id, film_dict))
    return json.dumps(film_database)

def get_film(film_name):
    app.logger.info('{}: Getting film {}'.format(get_debug_string(), film_name))
    for item in film_database:
        if item['name'] == film_name:
            return json.dumps(item)
    abort(404)

def get_debug_string():
    return '(service {}):(hostname {})'.format(os.environ['SERVICE_NAME'], socket.gethostname())


def populate_film_database():
    global film_database
    film_1 = {
        'id': str(uuid.uuid4()),
        'name': 'Citizen Kane',
        'language': 'English'
    }
    film_2 = {
        'id': str(uuid.uuid4()),
        'name': 'Bangalore Days',
        'language': 'Malayalam'
    }
    film_3 = {
        'id': str(uuid.uuid4()),
        'name': 'Agneepath',
        'language': 'Hindi'
    }
    film_database = [film_1, film_2, film_3]


if __name__ == '__main__':
    populate_film_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
    app.logger.info("Film Service has started")
