import pika
import os
import time

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
INPUT_FILE = 'input.txt'
QUEUE_NAME = os.getenv('QUEUE_NAME')


for i in range(10):
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

def publish_messages():
    with open(INPUT_FILE, 'r') as file:
        for line in file:
            message = line.strip()
            if message:
                channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=message)
                print(f'Sent: {message}')
                time.sleep(1)

if __name__ == '__main__':
    publish_messages()
