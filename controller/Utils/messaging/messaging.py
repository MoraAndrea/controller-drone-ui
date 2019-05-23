import json
import uuid

import pika

from controller.Utils import singleton
from controller.config.config import Configuration


class Messaging(object, metaclass=singleton.Singleton):
    """
    This class manages exchange of messages with the neighborhood through rabbitmq.
    """

    def __init__(self, broker=None):
        self.configuration = Configuration()

        self._broker_host = broker
        self._connections = dict()
        self._channels = dict()
        self._message_handler = None

    def connect(self):

        connection_id = uuid.uuid4().hex
        connection = self._rabbitmq_connect(self._broker_host,self.configuration.USERNAME, self.configuration.PASSWORD)
        channel = connection.channel()
        self._connections[connection_id] = connection
        self._channels[connection_id] = channel

        # create exchange for federation
        exchange_name = self.configuration.EXCHANGE
        self.create_exchange(connection_id,exchange=exchange_name, exchange_type='direct')

        return connection_id

    def disconnect(self,connection_id):
        connection=self._connections.pop(connection_id)
        connection.close()

    @staticmethod
    def _rabbitmq_connect(broker_host,username, password):
        credentials = pika.PlainCredentials(username,password)
        parameters = pika.ConnectionParameters(broker_host, 5672, '/', credentials)
        return pika.BlockingConnection(parameters)

    def send_message(self, connection_id, dst, message, exchange_name, local=False):
        if connection_id not in self._channels:
            print(connection_id+" not found")
        if local:
            exchange = ''
        else:
            exchange =self.configuration.EXCHANGE
        self._channels[connection_id].queue_declare(queue=dst)
        if exchange != '':
            self._channels[connection_id].queue_bind(exchange=exchange_name, queue=dst)
        self._channels[connection_id].basic_publish(exchange=exchange_name, routing_key=dst, body=json.dumps(message.to_dict()))

    def create_bind_queue(self,connection_id, name, exchange_name):
        self._channels[connection_id].queue_declare(queue=name)
        self._channels[connection_id].queue_bind(exchange=exchange_name, queue=name)

    def create_exchange(self,connection_id, exchange, exchange_type):
        self._channels[connection_id].exchange_declare(exchange, exchange_type)

    def start_consuming(self,connection_id):
        if connection_id not in self._channels:
            print(connection_id+" not found")
        self._channels[connection_id].start_consuming()

    def stop_consuming(self,connection_id):
        if connection_id not in self._channels:
            print(connection_id+" not found")
        self._channels[connection_id].stop_consuming()
