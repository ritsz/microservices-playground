#!/bin/bash

curl -m 2 -v -X POST localhost:8080/users/rritesh

curl -m 2 -v -X GET https://localhost:8443/users/rritesh --insecure | jq .

curl -m 2 -v -X DELETE https://localhost:8443/users/rritesh --insecure

curl -m 2 -v -X GET http://localhost:8080/users/rritesh | jq .
