import os
import pika
import time
from cassandra.cluster import Cluster, NoHostAvailable

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
QUEUE_NAME = os.getenv('QUEUE_NAME')
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST')
KEYSPACE = 'test'


for _ in range(10):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        print('Connected to RabbitMQ')
        break
    except Exception as e:
        print(f'Failed to connect to RabbitMQ: {e}')
        time.sleep(5)
else:
    raise Exception('Failed to connect to RabbitMQ after multiple attempts')


for i in range(10):
    try:
        cluster = Cluster([CASSANDRA_HOST])
        session = cluster.connect()
        session.execute(f"CREATE KEYSPACE IF NOT EXISTS {KEYSPACE} WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}")
        session.set_keyspace(KEYSPACE)
        session.execute('CREATE TABLE IF NOT EXISTS messages (id UUID PRIMARY KEY, message TEXT)')
        print('Connected to Cassandra')
        break
    except NoHostAvailable:
        print('Failed to connect to Cassandra, retrying...')
        time.sleep(5)
else:
    raise Exception('Failed to connect to Cassandra after multiple attempts')


def callback(ch, method, properties, body):
    message = body.decode()
    print(f'Received: {message}')
    try:
        session.execute(
            'INSERT INTO messages (id, message) VALUES (uuid(), %s)',
            (message,)
        )
        print('Message saved to Cassandra')
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f'Failed to save message to Cassandra: {e}')

channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
print('Waiting for messages...')
channel.start_consuming()
