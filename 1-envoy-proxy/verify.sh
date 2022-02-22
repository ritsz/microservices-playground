#!/bin/bash -e

_curl='curl --connect-timeout 5 --max-time 10 --retry 5 --retry-max-time 40'

startup () {
	docker-compose build
	docker-compose up -d
}

populate () {

	$_curl --fail -X POST http://127.0.0.1:8080/films --data "{
		'name': 'Citizen Kane',
		'language': 'English'
	}"
	$_curl --fail -X POST http://127.0.0.1:8080/films --data "{
		'name': 'Agneepath',
		'language': 'English'
	}"
}

checks () {
	populate

	sleep 2
	$_curl --fail -X GET http://127.0.0.1:8080/films
	$_curl --fail -X GET http://127.0.0.1:8080/films?name=Citizen%20Kane
	$_curl --fail -X GET http://127.0.0.1:8080/ratings?name=Agneepath
	$_curl --fail -X POST http://127.0.0.1:8080/films --data "{
		'name': 'Titanic',
		'language': 'English'
	}"

	$_curl --fail -X GET http://127.0.0.1:8080/films?name=Titanic
	echo $?
	$_curl --fail -X GET http://127.0.0.1:8080/ratings?name=Titanic
	echo $?
}

scale () {
	docker-compose scale film-service=5
	docker-compose scale rating-service=3
}

cleanup () {
	docker-compose down
}

trap 'cleanup' EXIT

set -x
startup
checks

echo "Scaling services"
scale
checks
set +x
