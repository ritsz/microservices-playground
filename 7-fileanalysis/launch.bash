#!/usr/bin/env bash

set -x

echo "Build images"
echo "Start containers"
docker compose -f docker-compose.yaml  --env-file env.config up -d --force-recreate --build

echo "Sleeping"
sleep 15

curl -i -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/

curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d '{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname": "postgres",
    "database.server.name": "postgres-database"
  }
}'

curl -i -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/

set +x
