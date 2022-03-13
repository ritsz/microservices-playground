#!/bin/bash

curl -v -X POST 192.168.1.36:8080/users/rritesh

curl -v -X GET https://192.168.1.36:8443/users/rritesh --insecure | jq .
