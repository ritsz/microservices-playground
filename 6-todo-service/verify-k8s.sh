#!/bin/bash

_curl='curl --insecure'

create_kubernetes_cluster () {
	minikube start
}

create_images () {
	docker-compose build
}


load_images () {
	minikube images load frontend-proxy users-service tasks-service
	minikube images ls
}

start_observability () {
	kubectl apply -f kubernetes/0-setup --server-side=true
	kubectl apply -f kubernetes/1-kube-prometheus-manifests
	kubectl apply -f kubernetes/2-logging
}

create_namespaces () {
	kubectl apply -f kubernetes/namespace.yaml
}

create_certificates () {
	kubectl apply -f kubernetes/3-certificates
	kubectl rollout status -w deployments/cert-manager-cainjector -n cert-manager
	kubectl rollout status -w deployments/cert-manager -n cert-manager 

	sleep 10
}

start_applications () {
	create_namespaces
	
	create_certificates

	kubectl apply -f kubernetes/4-applications

	kubectl rollout status -w deployments/frontend-proxy-deployment -n applications
	kubectl rollout status -w deployments/mongodb-deployment -n applications

	minikube service frontend-proxy -n applications --url=true 

	sleep 10
}

startup () {
	echo "[Step-1] Create kubernetes cluster."
	# create_kubernetes_cluster

	echo "[Step-2] Build and load images."
	create_images	
	# load_images

	echo "[Step-3] Deploy application in kubernetes cluster."
	start_applications
} 

scale () {
	echo "Scale services"
}

checks () {
	echo "### Perform checks ###"

	kubectl get all -n applications

	$_curl -v -X POST http://localhost:8080/users/foo
	$_curl -v -X POST http://localhost:8080/users/foo/task --data "{'desc' : 'This is a verification and integration task' }"
	$_curl -v -X POST http://localhost:8080/users/foo/task --data "{'desc' : 'This is another simple task' }"

	$_curl -v -X POST http://localhost:8080/users/bar
	$_curl -v -X POST http://localhost:8080/users/bar/task --data "{'desc' : 'This is user-2's task' }"

	$_curl -v -X GET https://localhost:8443/users
	$_curl -v -X GET https://localhost:8443/tasks

	$_curl -v -X POST https://localhost:8443/tasks/complete?user=foo
	$_curl -v -X GET https://localhost:8443/tasks

	$_curl -v -X DELETE https://localhost:8443/users/foo
	$_curl -v -X GET https://localhost:8443/users
	$_curl -v -X GET https://localhost:8443/tasks
	
	echo "### Checks done ###"
}

cleanup () {
	echo "### CLEANUP ###"
	# kubectl delete -f kubernetes/namespace.yaml
	# minikube delete
	echo "### DONE ###"
}

trap 'cleanup' EXIT

set -x
startup
checks

echo "Scaling services"
scale
checks
set +x