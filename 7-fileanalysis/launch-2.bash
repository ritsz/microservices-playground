#!/usr/bin/env bash

set -x

cp Dockerfiles/config/nginx.conf /var/nginx.conf

mkdir /mnt2/data-1
mkdir /mnt2/data-2

echo "Build images"
echo "Start containers"

docker compose -f docker-compose-2.yaml --env-file env.config up -d --force-recreate --build
set +x
