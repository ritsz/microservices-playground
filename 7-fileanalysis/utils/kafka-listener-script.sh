#! /bin/bash

/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic postgres-database.public.file_entity  --from-beginning
