import json
import logging
import os
import socket
from flask import Flask, abort, request
from flask_opentracing import FlaskTracing
from jaeger_client import Config

SERVICE_NAME = os.environ.get("SERVICE_NAME")
FLASK_PORT = 6000

app = Flask(__name__)
rating_database = list()


def init_tracer():
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config = Config(
        config={  # usually read from some yaml config
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'local_agent': {
                'reporting_host': "jaeger",
                'reporting_port': 6831,
            },
            'logging': True,
        },
        service_name=SERVICE_NAME,
    )
    return config.initialize_tracer()


tracer = FlaskTracing(init_tracer, True, app)


@app.before_request
def log_request_info():
    app.logger.info('####\n\n %s Headers: %s\n\n####', get_debug_string(), get_headers())


@app.route('/management/readiness')
def readiness():
    return 'Ready and Healthy', 200


@app.route('/ratings')
def get_ratings():
    film_name = request.args.get('name')
    if film_name:
        return get_rating(film_name)
    else:
        app.logger.info('%s: Getting all film ratings %s', get_debug_string(), rating_database)
        return json.dumps(rating_database)


@app.route('/ratings/<id>', methods=['GET'])
def get_rating_by_id(id):
    app.logger.info('%s: Getting film rating %s', get_debug_string(), id)
    for item in rating_database:
        if item['id'] == id:
            return json.dumps(item)
    abort(404)


@app.route('/ratings', methods=['POST'])
def post_rating():
    global rating_database
    film_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    rating_database.append(film_dict)
    app.logger.info('%s: Added film %s: %s', get_debug_string(), id, film_dict)
    return json.dumps(rating_database)


def get_headers():
    # Headers that are received from incoming RPC, and propagated to outgoing RPCs.
    TRACE_HEADERS_TO_PROPAGATE = [
        'X-Ot-Span-Context',
        'X-Request-Id',
        # Zipkin headers
        'X-B3-TraceId',
        'X-B3-SpanId',
        'X-B3-ParentSpanId',
        'X-B3-Sampled',
        'X-B3-Flags',
        # Jaeger header (for native client)
        "uber-trace-id",
        # SkyWalking headers.
        "sw8"
    ]
    extract_headers = {}
    for header in TRACE_HEADERS_TO_PROPAGATE:
        if header in request.headers:
            extract_headers[header] = request.headers[header]
        else:
            extract_headers[header] = None
    return extract_headers


def get_rating(film_name):
    app.logger.info('%s: Getting film %s', get_debug_string(), film_name)
    for item in rating_database:
        if item['name'] == film_name:
            return json.dumps(item)
    abort(404)


def get_debug_string():
    return '(service {}):(hostname {})'.format(SERVICE_NAME, socket.gethostname())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
    app.logger.info("Ratings Service has started")
