#!/usr/bin/env bash

set -x

cp Dockerfiles/config/nginx.conf /var/nginx.conf

mkdir /mnt2/data-1
mkdir /mnt2/data-2

echo "Build images"
echo "Start containers"

docker compose -f docker-compose.yaml --env-file ev.config up -d --force-recreate --build
set +x