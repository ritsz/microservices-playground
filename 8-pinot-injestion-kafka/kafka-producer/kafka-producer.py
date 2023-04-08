#! /usr/local/bin/python3

from kafka import KafkaProducer
from kafka.producer.future import FutureRecordMetadata
import requests
import json
import os
import time

# Github token to get access to github APIs
github_token = os.environ.get('GITHUB_TOKEN')

# Define the list of repositories to track
github_repos = os.environ.get('GITHUB_REPOS').split(',')
print("Repos: {}".format(github_repos))

# Kafka configs
kafka_broker = os.environ.get('KAFKA_BROKER')
print("Broker Location: {}".format(kafka_broker))

kafka_github_events_topic = os.environ.get('KAFKA_TOPIC')
print("Topic: {}".format(kafka_github_events_topic))

# Define the request headers for Github APIs
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer {}".format(github_token),
    "X-GitHub-Api-Version": "2022-11-28"
}

time.sleep(5)

# Define the Kafka producer
producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Check if producer is connected to the broker
if producer.bootstrap_connected():
    print("Producer connected to broker")
else:
    print("Producer connection failed")
    exit(1)

# Define the GitHub API endpoint and parameters
endpoint = "https://api.github.com/repos/{}/events"
params = {"per_page": "100"}


while True:
    # Loop through the list of repositories
    for repo in github_repos:
        # Make a request to the GitHub API with authentication
        url = endpoint.format(repo)
        response = requests.get(url, params=params, headers=headers)
        print("Repo [{}]: response: {}".format(url, response))
        count = 0
        
        # Check if the response was successful
        if response.status_code == 200:
            # Loop through the list of events
            for event in response.json():
                # Build the message to send to Kafka
                message = {
                    "repo": repo,
                    "event": event
                }
                
                # Send the message to Kafka
                future = producer.send("github-events", value=message)
                
                # Log the message
                print("Sent message to Kafka for repo: {}".format(url))

                # Block for 'synchronous' sends
                try:
                    record_metadata = future.get(timeout=10)
                    count = count + 1
                except KafkaError as e:
                    print(f"Error while sending message to Kafka: {e}")
        else:
            # Log the error
            print("Error retrieving events for repo {}: {}".format(repo, response.text))
        print(f"[{count}] Message(s) sent to Kafka")
    time.sleep(5)
