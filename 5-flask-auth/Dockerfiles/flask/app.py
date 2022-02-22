import functools
import json
import os
import jwt
import logging
import uuid

import requests
from authlib.integrations.requests_client import OAuth2Session
from flask import Flask, make_response, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import check_password_hash, generate_password_hash

from model import User, Permissions

app = Flask(__name__)
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY") or os.urandom(24)
app.config['SECRET_KEY'] = 'thisismysecretkeydonotstealit'

# logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

login_manager = LoginManager()
login_manager.init_app(app)

GOOGLE_CLIENT_ID = os.environ.get("FN_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("FN_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
REDIRECT_URL = os.environ.get("FN_AUTH_REDIRECT_URI", None)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


def no_cache(view):
    @functools.wraps(view)
    def no_cache_impl(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return functools.update_wrapper(no_cache_impl, view)


def check_login(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        headers = request.headers
        if current_user.is_authenticated:
            app.logger.info("User %s is authenticated", current_user.name)
            return func(*args, **kwargs)

        token = headers.get('x-auth-token', None)
        if not token:
            return "Forbidden", 403
        try:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], "HS256")
            app.logger.info("Token %s", decoded_token)
        except Exception as ex:
            app.logger.error("Exception %s", ex)
            return "Forbidden", 403
        return func(*args, **kwargs)
    return decorator


@login_manager.user_loader
def load_user(user_id):
    app.logger.info("Loading user_id %s", user_id)
    return User.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


@app.before_request
def log_request_info():
    app.logger.info('\n\n\n New Request\n######\n## URL: %s\n## User: %s \n## Authorization: %s \n## Headers: %s\n######',
        request.url,
        current_user,
        request.authorization,
        request.headers)


@app.route('/add-user')
def add_user():
    args = request.args
    name = args.get('username')
    password = args.get('password')
    user_id = str(uuid.uuid4())
    app.logger.info("Adding user %s hash password %s", name, password)
    hashed_password = generate_password_hash(password, method='sha256')
    User.create(id_=user_id, name=name, password=hashed_password, permissions=Permissions.WRITE)
    return user_id, 200


@app.route('/login-basic-jwt')
def login_jwt():
    auth = request.authorization
    if not auth or not auth.password or not auth.username:
        return make_response('Login requires basic authorization', 401,
                             {'WWW-Authenticate': 'Basic realm="Login Required"'})

    user = User.get_by_name(auth.username)
    if not user:
        return make_response('Invalid Credentials!', 401)

    if not check_password_hash(user.password, auth.password):
        return make_response('Invalid Credentials!', 401)

    token = jwt.encode({'user': user.name, 'perm': user.permissions}, app.config['SECRET_KEY'])
    login_user(user)
    app.logger.info("Current User %s", current_user.name)
    return jsonify({'token': token})


@app.route("/login")
@no_cache
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    app.logger.info("Google authorization endpoint %s", authorization_endpoint)

    session = OAuth2Session(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                            scope='openid email profile',
                            redirect_uri=REDIRECT_URL)

    request_uri, state = session.create_authorization_url(authorization_endpoint)
    app.logger.info("Authorize using Endpoint %s Callback %s. Session %s", authorization_endpoint, REDIRECT_URL,
                    repr(session))
    return redirect(request_uri, code=302)


@app.route('/google/auth')
@no_cache
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    req_state = request.args.get('state', default=None, type=None)
    app.logger.info("Returned to callback. URL %s,\nCode %s,\nState %s", request.url, code, req_state)

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    app.logger.info("Google token endpoint %s", token_endpoint)

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    app.logger.info("Requesting for tokens: Token URL %s\nHeaders %s\nBody %s", token_url, headers, body)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    app.logger.info("Token Response %s", json.dumps(token_response.json(), indent=3))

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    app.logger.info("Requesting for user information. User Info URL %s Headers %s Body %s", uri, headers, body)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    app.logger.info("User Response %s", json.dumps(userinfo_response.json(), indent=3))

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        app.logger.info("User ID %s Email %s Name %s", unique_id, users_email, users_name)
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture, permissions=Permissions.ADMIN
    )
    # Doesn't exist? Add to database
    if not User.get(unique_id):
        insert_id = User.create(unique_id, users_name, users_email, picture)
        app.logger.info("Inserted %s as ID %s", user, insert_id)

    # Begin user session by logging the user in
    login_user(user)
    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@check_login
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/protected")
@check_login
def protected_resource():
    return jsonify({'message': 'You are a privileged user'})


@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8040, debug=True)
