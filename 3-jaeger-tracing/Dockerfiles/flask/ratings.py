import functools
import json
import os
import socket

import requests
from flask import Flask, abort, request
from py_zipkin.encoding import Encoding
from py_zipkin.zipkin import ZipkinAttrs, zipkin_span

SERVICE_NAME = os.environ.get("SERVICE_NAME")
ZIPKIN_DSN = os.environ.get("ZIPKIN_DSN", "http://jaeger:9411/api/v2/spans")
FLASK_PORT = 6000

app = Flask(__name__)
rating_database = list()

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


def default_handler(encoded_span):
    return requests.post(
        ZIPKIN_DSN,
        data=encoded_span,
        headers={"Content-Type": "application/json"},
    )


def zipkin_start_span(span_name):
    def zipkin_start_span_decorator(func):
        @functools.wraps(func)
        def zipkin_start_span_inner(*args,  **kwargs):
            headers = get_headers()
            with zipkin_span(
                    service_name=SERVICE_NAME,
                    zipkin_attrs=ZipkinAttrs(
                        trace_id=headers["X-B3-TraceId"],
                        span_id=headers["X-B3-SpanId"],
                        parent_span_id=headers["X-B3-ParentSpanId"],
                        flags=headers['X-B3-Flags'],
                        is_sampled=headers["X-B3-Sampled"],
                    ),
                    span_name=span_name,
                    transport_handler=default_handler,
                    port=FLASK_PORT,
                    sample_rate=100,
                    encoding=Encoding.V2_JSON
            ):
                return func(*args, **kwargs)
        return zipkin_start_span_inner
    return zipkin_start_span_decorator


@app.before_request
def log_request_info():
    app.logger.info('####\n\n %s Headers: %s\n\n####', get_debug_string(), get_headers())


@app.route('/ratings')
@zipkin_start_span(span_name="GET /ratings")
def get_ratings():
    film_name = request.args.get('name')
    if film_name:
        return get_rating(film_name)
    else:
        app.logger.info('%s: Getting all film ratings %s', get_debug_string(), rating_database)
        return json.dumps(rating_database)


@app.route('/ratings/<id>', methods=['GET'])
@zipkin_start_span(span_name="GET /ratings/<id>")
def get_rating_by_id(id):
    app.logger.info('%s: Getting film rating %s', get_debug_string(), id)
    for item in rating_database:
        if item['id'] == id:
            return json.dumps(item)
    abort(404)


@app.route('/ratings', methods=['POST'])
@zipkin_start_span(span_name="POST /ratings")
def post_rating():
    global rating_database
    film_dict = json.loads(request.get_data().decode('utf-8').replace("\'", "\""))
    rating_database.append(film_dict)
    app.logger.info('%s: Added film %s: %s', get_debug_string(), id, film_dict)
    return json.dumps(rating_database)


def get_headers():
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
