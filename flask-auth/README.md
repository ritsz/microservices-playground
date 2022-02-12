## OpenID Connect and Session Management with Flask
* There are two very popular and important specifications called OAuth 2 and OpenID Connect (OIDC).
* OIDC is built on top of OAuth 2, adding a few new ideas and concepts.
* This application will let a user use a Google Login button to log in.
* To do that, Google needs to know about this application. We can register your application as a client to Google.
* Cookies are used to track the request from a user in a particular session. The server (our application in this case), returns a `SetCookie` header with a session cookie in the response.
* The client (browser or `curl`) can set the session cookie in the header of subsequent requests to allow the server to track the session context.

### OIDC Handshake flow
* To request information on behalf of a user, the application must become a client to the **authentication server**, also known as the **provider** (Google authentication servers in this example).
* You register a third-party application as a client to the provider:
  * You receive unique client credentials from the provider.
  * You’ll use these client credentials to authenticate (prove who you are) to the provider later on.
* The client sends a request to the provider’s **authorization URL**.
* The provider asks the user to authenticate (prove who they are)
* The provider asks the user to consent to the client acting on their behalf:
  * Usually this includes limited access, and it’s made clear to the user what the client is asking for.
  * This is like when you have to approve an app on your phone to have access to location or contacts.
* The provider sends the client a unique **authorization code**.
* The client sends the authorization code back to the provider’s **token URL**.
* The provider sends the client tokens to use with other provider URLs on behalf of the user.
* The userinfo endpoint will return information about the user after you’ve gone through the OAuth 2 flow. This will include their email and some basic profile information you’ll use in your application.

### Application
* The flask application has an `index` route that checks if the `current_user` is authenticated. It shows a login page for anonymous users and a profile page for logged in users.
* `current_user` is a global variable that `flask_login` provides to track the status of the user in the current session.
* The `login`, `callback` and `logout` functions help in the login/logout of the user using Google authentication servers.
* The `/protected` URI is accessible only to users that have logged in.
* We use `check_login` decorator to decorate functions that need to be protected.
* `check_login` checks if either of these two is true:
  * `current_user.is_authenticated`: This happens when a user session has been authenticated.
  * Request header `x-auth-token` has tokens that allow access to this resource.

### User Persistence
* The user information is persisted in a mongodb database.
* MongoDB stores data records as documents (specifically BSON documents) which are gathered together in collections.
* A database stores one or more collections of documents.
* Login to mongodb.
  ```bash
    $ docker ps  
    CONTAINER ID   IMAGE             COMMAND                  CREATED          STATUS          PORTS                      NAMES
    3906c5f009b0   auth-app:latest   "/app/run.sh"            20 minutes ago   Up 20 minutes   0.0.0.0:8040->8040/tcp     auth-app
    eb8571087284   mongo             "docker-entrypoint.s…"   10 days ago      Up 20 minutes   0.0.0.0:27017->27017/tcp   mongodb

    $ docker exec -it mongodb bash

    root@eb8571087284:/$ mongosh -u root -p example
  ```
* Get the list of DBs. Our application uses `login_db`, and `login_collection` collection
```bash
  test> show dbs
  admin      102 kB
  config     111 kB
  local     73.7 kB
  login_db  73.7 kB

  test> use login_db
  switched to db login_db
  login_db>

  login_db> show collections
  login_collection
  login_db>
```
* Query all the documents in this collection, using the empty `{}` query:
```bash
  login_db> db.login_collection.find({})
  [
  {
    _id: ObjectId("61f97ec398943ce9f12dfc4f"),
    user_id: '8807e121-d0da-4e21-9418-2bb1d6296ae5',
    name: 'apple',
    email: '',
    profile_pic: '',
    password: 'sha256$JbtGJwMCzbPUEqz1$96fe2facc13df50678b95f691c5c1c5d1f53a0a12a483cc14b94bb417e93ad8a',
    permissions: 'Permissions.WRITE'
  },
  {
    _id: ObjectId("61f97fc623363cb88047bff0"),
    user_id: '5583836a-cafc-4d66-aa17-a96ff3b0b141',
    name: 'root',
    email: '',
    profile_pic: '',
    password: 'sha256$7WhdVqN7T9dlmI1o$5b86e5720fb1fcb4cfc2e256551ef32a12d7dc4038fc5a8034ffb12ad5b4b9d8',
    permissions: 'Permissions.WRITE'
  },
  {
    _id: ObjectId("61f9804423363cb88047bff5"),
    user_id: 'bdf1d38a-275c-45bb-985c-b9cf120df781',
    name: 'foobar',
    email: '',
    profile_pic: '',
    password: 'sha256$L2yrvERH5SU111bH$e5558793817f26b9d6aece65cf6c47c4a879a0635298796edb3b10f7bfbe6472',
    permissions: 'Permissions.WRITE'
  }
  ]
  login_db>
```
* Flask login uses a `User` class that is derived from `UserMixin`.
* Flask-login requires a User model with the following properties:
  * has an `is_authenticated()` method that returns True if the user has provided valid credentials
  * has an `is_active()` method that returns True if the user’s account is active
  * has an `is_anonymous()` method that returns True if the current user is an anonymous user
  * has a `get_id()` method which, given a User instance, returns the unique ID for that object
* `UserMixin` class provides the implementation of this properties.
* It's the reason you can call for example `is_authenticated` to check if login credentials provide is correct or not instead of having to write a method to do that yourself.
* Flask-login also requires you to define a `user_loader` function which, given a user ID, returns the associated user object.
* In the case of this application, the `user_loader` loads the user object from MongoDB.
```python
@login_manager.user_loader
def load_user(user_id):
    app.logger.info("Loading user_id %s", user_id)
    return User.get(user_id)
```

### Testing session management
* To test session management, we introduce a unprotected API for creating users at `/add-user`.
* The `User` document is created and persisted into MongoDB.
#### Adding User
* Start with an empty collection:
```bash
  login_db> db.login_collection.drop({})
  true
  login_db> db.login_collection.find({})

  login_db>
```
* Execute a REST API to add-user:
```bash
  curl http://localhost:8040/add-user\?username=foobar\&password=acme
  56268fac-33d8-42af-aa22-6c1b7324155e%
```
* Logs show that the current user is anonymous and we add a user.
  ```
  New Request
  ######
  ## URL: http://localhost:8040/add-user?username=foobar&password=acme
  ## User: <flask_login.mixins.AnonymousUserMixin object at 0x7f9da826d750>
  ## Authorization: None
  ## Headers: Host: localhost:8040
  User-Agent: curl/7.64.1
  Accept: */*

  ######
  [2022-02-12 07:47:53,329] INFO in app: Adding user foobar hash password acme
  172.22.0.1 - - [12/Feb/2022 07:47:53] "GET /add-user?username=foobar&password=acme HTTP/1.1" 200 -
  ```
* New user added in MongoDB
```bash
  login_db> db.login_collection.find({})
  [
    {
      _id: ObjectId("620766298b6c52307ce86fed"),
      user_id: '56268fac-33d8-42af-aa22-6c1b7324155e',
      name: 'foobar',
      email: '',
      profile_pic: '',
      password: 'sha256$3qHnpwNZppNMoHFV$ded82205f217dc4b29d3af553dd933a680063dd461fc30d9f2a30c6c473f2ba4',
      permissions: 'Permissions.WRITE'
    }
  ]
  login_db>
```
#### User Login
* Using the username/password, user logs in. A token and a cookie is returned to the client.
  ```
  $ curl -vsu 'foobar:acme' http://localhost:8040/login-basic-jwt
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to localhost (127.0.0.1) port 8040 (#0)
  * Server auth using Basic with user 'foobar'
  > GET /login-basic-jwt HTTP/1.1
  > Host: localhost:8040
  > Authorization: Basic Zm9vYmFyOmFjbWU=
  > User-Agent: curl/7.64.1
  > Accept: */*
  >
  * HTTP 1.0, assume close after body
  < HTTP/1.0 200 OK
  < Content-Type: application/json
  < Content-Length: 158
  < Vary: Cookie
  < Set-Cookie: session=.eJwtjjEOwzAIAP_iuZZsMBjymQgbrHZNmqnq35uhN99J90n7OuJ8pu19XPFI-8vTlggkuBspVwhsNguHTDLhAuJIsJogNZcqrA0VpzcsoBiuN25IXkW1u8RgimVCpE2DieddWOCI6qxCY1i3acUrS_F-ix0x3SPXGcf_hoFl2cyILrmBrWwGkHnW0RFaJYr0_QEbczcP.Ygdrjw.7gEyRBdZloRJmbmcHRB2kni0gpQ; HttpOnly; Path=/
  < Server: Werkzeug/2.0.3 Python/3.7.12
  < Date: Sat, 12 Feb 2022 07:52:19 GMT
  <
  {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZm9vYmFyIiwicGVybSI6IlBlcm1pc3Npb25zLldSSVRFIn0.8jw7-lIOtdwvHIsyACRCDyOH3B4zQJNfi7Z2orfMqos"
  }
  * Closing connection 0
  ```

* Token `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZm9vYmFyIiwicGVybSI6IlBlcm1pc3Npb25zLldSSVRFIn0.8jw7-lIOtdwvHIsyACRCDyOH3B4zQJNfi7Z2orfMqos` is returned and a session cookie `.eJwtjjEOwzAIAP_iuZZsMBjymQgbrHZNmqnq35uhN99J90n7OuJ8pu19XPFI-8vTlggkuBspVwhsNguHTDLhAuJIsJogNZcqrA0VpzcsoBiuN25IXkW1u8RgimVCpE2DieddWOCI6qxCY1i3acUrS_F-ix0x3SPXGcf_hoFl2cyILrmBrWwGkHnW0RFaJYr0_QEbczcP.Ygdrjw.7gEyRBdZloRJmbmcHRB2kni0gpQ` is added to response header.
* The token is created by the application and the client can set it in request headers to authorize API requests.
```python
  token = jwt.encode({'user': user.name, 'perm': user.permissions}, app.config['SECRET_KEY'])
```
* The current user is logged in and flask_login tracks this authenticated session using cookies.
```python
  login_user(user)
```
* From the logs, user login starts anonymous, but eventually after `login_user`, the current user is changed to the `user` object passed to `login_user` function.
  ```
  New Request
  ######
  ## URL: http://localhost:8040/login-basic-jwt
  ## User: <flask_login.mixins.AnonymousUserMixin object at 0x7f9da8267110>
  ## Authorization: {'username': 'foobar', 'password': 'acme'}
  ## Headers: Host: localhost:8040
  Authorization: Basic Zm9vYmFyOmFjbWU=
  User-Agent: curl/7.64.1
  Accept: */*

  ######
  [2022-02-12 07:52:19,202] INFO in app: Current User foobar
  172.22.0.1 - - [12/Feb/2022 07:52:19] "GET /login-basic-jwt HTTP/1.1" 200 -
  ```

#### Accessing protected resources
* The protected resource can be accessed using either token or using an authenticated session cookie.
##### Token
* The token received from `login-basic-jwt` is passed in `x-auth-token` header, which is where the application is expecting a token.
* The client is able to access the protected resources with the correct token.
  ```bash
  curl  http://localhost:8040/protected --header "x-auth-token: 12345"
  Forbidden%

  $ curl  http://localhost:8040/protected --header "x-auth-token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZm9vYmFyIiwicGVybSI6IlBlcm1pc3Npb25zLldSSVRFIn0.8jw7-lIOtdwvHIsyACRCDyOH3B4zQJNfi7Z2orfMqos"
  {
    "message": "You are a privileged user"
  }
  ```
* In logs, we see that since the session key is not used, this is still an anonymous user. But since the token is valid, the user is allowed to access the resource.
  ```
  New Request
  ######
  ## URL: http://localhost:8040/protected
  ## User: <flask_login.mixins.AnonymousUserMixin object at 0x7f9da826c210>
  ## Authorization: None
  ## Headers: Host: localhost:8040
  User-Agent: curl/7.64.1
  Accept: */*
  X-Auth-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZm9vYmFyIiwicGVybSI6IlBlcm1pc3Npb25zLldSSVRFIn0.8jw7-lIOtdwvHIsyACRCDyOH3B4zQJNfi7Z2orfMqos

  ######
  [2022-02-12 08:04:05,834] INFO in app: Token {'user': 'foobar', 'perm': 'Permissions.WRITE'}
  172.22.0.1 - - [12/Feb/2022 08:04:05] "GET /protected HTTP/1.1" 200 -
  ```

##### Session Cookie
* Sending back the cookie that the server sent to the client is a way of managing an authenticated session.
  ```
  $ curl  -vs http://localhost:8040/protected --cookie "session=.eJwtjjEOwzAIAP_iuZZsMBjymQgbrHZNmqnq35uhN99J90n7OuJ8pu19XPFI-8vTlggkuBspVwhsNguHTDLhAuJIsJogNZcqrA0VpzcsoBiuN25IXkW1u8RgimVCpE2DieddWOCI6qxCY1i3acUrS_F-ix0x3SPXGcf_hoFl2cyILrmBrWwGkHnW0RFaJYr0_QEbczcP.Ygdrjw.7gEyRBdZloRJmbmcHRB2kni0gpQ"

  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to localhost (127.0.0.1) port 8040 (#0)
  > GET /protected HTTP/1.1
  > Host: localhost:8040
  > User-Agent: curl/7.64.1
  > Accept: */*
  > Cookie: session=.eJwtjjEOwzAIAP_iuZZsMBjymQgbrHZNmqnq35uhN99J90n7OuJ8pu19XPFI-8vTlggkuBspVwhsNguHTDLhAuJIsJogNZcqrA0VpzcsoBiuN25IXkW1u8RgimVCpE2DieddWOCI6qxCY1i3acUrS_F-ix0x3SPXGcf_hoFl2cyILrmBrWwGkHnW0RFaJYr0_QEbczcP.Ygdrjw.7gEyRBdZloRJmbmcHRB2kni0gpQ
  >
  * HTTP 1.0, assume close after body
  < HTTP/1.0 200 OK
  < Content-Type: application/json
  < Content-Length: 45
  < Vary: Cookie
  < Server: Werkzeug/2.0.3 Python/3.7.12
  < Date: Sat, 12 Feb 2022 08:12:53 GMT
  <
  {
    "message": "You are a privileged user"
  }
  * Closing connection 0
  ```
* From the logs, we see that `user_loader` is called that loads the user object for which this session cookie was created. The session cookie maps to user_id `56268fac-33d8-42af-aa22-6c1b7324155e` which is our `foobar:acme` user.
```
[2022-02-12 08:12:53,830] INFO in app: Loading user_id 56268fac-33d8-42af-aa22-6c1b7324155e
```
* Then we see that the `current_user` is set to `foobar:acme` and the request is handled in that user's context.
  ```
  [2022-02-12 08:12:53,829] INFO in app:
   New Request
  ######                                                                                                                                                                                   ## URL: http://localhost:8040/protected
  ## User: <model.User object at 0x7f9da826d450>
  ## Authorization: None
  ## Headers: Host: localhost:8040
  User-Agent: curl/7.64.1
  Accept: */*
  Cookie: session=.eJwtjjEOwzAIAP_iuZZsMBjymQgbrHZNmqnq35uhN99J90n7OuJ8pu19XPFI-8vTlggkuBspVwhsNguHTDLhAuJIsJogNZcqrA0VpzcsoBiuN25IXkW1u8RgimVCpE2DieddWOCI6qxCY1i3acUrS_F-ix0x3SPXGcf_hoFl
  2cyILrmBrWwGkHnW0RFaJYr0_QEbczcP.Ygdrjw.7gEyRBdZloRJmbmcHRB2kni0gpQ

  ######
  [2022-02-12 08:12:53,852] INFO in app: User foobar is authenticated
  172.22.0.1 - - [12/Feb/2022 08:12:53] "GET /protected HTTP/1.1" 200 -
  ```

### OIDC using google login
* The app also provides a `login` endpoint.
## TODO
