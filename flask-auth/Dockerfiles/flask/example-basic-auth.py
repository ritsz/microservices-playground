from flask import Flask, request, make_response
from functools import wraps

app = Flask(__name__)


def auth_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        app.logger.info(request.authorization)
        app.logger.info(request.headers)
        if request.authorization and request.authorization.username == 'username' and request.authorization.password == 'password':
            return func(*args, **kwargs)
        return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return decorated


@app.route('/basic-auth')
@auth_required
def index():
    return '<h1> You are logged in!!!!</h1>'


@app.route('/page')
@auth_required
def page():
    return '<h1> You are logged in to PAGE!!!!</h1>'


if __name__ == '__main__':
    app.run(debug=True)
