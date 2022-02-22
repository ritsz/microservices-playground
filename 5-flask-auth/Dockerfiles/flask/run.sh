#!/bin/bash

export FN_AUTH_REDIRECT_URI=http://localhost:8040/google/auth
export FN_BASE_URI=http://localhost:8040
export FN_FLASK_SECRET_KEY=1234567

export FLASK_APP=app.py
export FLASK_PORT=8040
export FLASK_DEBUG=1

export OAUTHLIB_INSECURE_TRANSPORT=1

python3 app.py
