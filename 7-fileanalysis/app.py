from flask import Flask
from kafka import KafkaConsumer
import json
 
app = Flask(__name__)
 
 
@app.route('/')
def hello_whale():
    consumer = KafkaConsumer('postgres-database.public.file_entity', bootstrap_servers='kafka:9092')
    msg = next(consumer)
    return json.loads(msg.value.decode())['payload']['after']
 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
