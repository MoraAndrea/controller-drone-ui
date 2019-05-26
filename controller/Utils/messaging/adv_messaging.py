import json
from threading import Thread

from controller.Utils import singleton
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.messaging import Messaging
from controller.config.config import Configuration


class Messaging_adv(object, metaclass=singleton.Singleton):

    def __init__(self, broker=None, queueAdv=None, queueUser=None):
        self._messaging = Messaging(broker)
        self._message_handler = None
        self.configuration = Configuration("config/config.ini")
        self.output_queue = queueAdv  # queue for read adv message
        self.output_queue_user= queueUser    # queue for read user request

    def register_handler_adv(self, connection_id, topic, handler,local=False):
        if connection_id not in self._messaging._channels:
            print(connection_id + " not found")

        if local:
            exchange = ''
        else:
            exchange = self.configuration.EXCHANGE

        self._messaging._channels[connection_id].queue_declare(queue=topic)
        if exchange != '':
            self._messaging._channels[connection_id].queue_bind(exchange=exchange, queue=topic)
        if handler is None:
            handler = self._adv_message_handler
        self._message_handler = handler
        self._messaging._channels[connection_id].basic_consume(
            self._message_callback_adv, queue=topic, no_ack=True)

    @staticmethod
    def _message_callback_adv(ch, method, properties, body):
        print(" [x] Received " + body.decode())
        self = Messaging_adv()
        message = AdvMessage()
        message.parse_dict(json.loads(body.decode()))
        self._message_handler(message)

    @staticmethod
    def _adv_message_handler(message):
        print("Received from " + message.owner + " for app " + message.app_name)

    def _adv_message_handler_enqueue(self, message):
        print("Received adv for app " + message.app_name)
        self.output_queue.put(message)

    def _user_req_message_handler_enqueue(self, message):
        print("Received adv for app " + message.app_name)
        self.output_queue_user.put(message)

    def send_adv_from_file(self, file, local=False):
        # connect
        connection_id = self._messaging.connect()

        if local:
            exchange = ''
        else:
            exchange = self.configuration.EXCHANGE

        message = AdvMessage()
        message.from_json(file)

        self._messaging.send_message(connection_id, self.configuration.QUEUE_ADV, message, exchange)

        self._messaging.disconnect(connection_id)

    def send_adv(self, message, local=False):
        # connect
        connection_id = self._messaging.connect()

        self._messaging.send_message(connection_id, self.configuration.QUEUE_ADV, message, local=False)

        self._messaging.disconnect(connection_id)

    def send_user_req(self, message, local=False):
        # connect
        connection_id = self._messaging.connect()

        self._messaging.send_message(connection_id, self.configuration.QUEUE_USER_REQ, message, local=True) # local True means that not use federation

        self._messaging.disconnect(connection_id)

    def consume_adv(self, handler_custom=None, local=False):
        # connect
        connection_id = self._messaging.connect()

        self.register_handler_adv(connection_id, self.configuration.QUEUE_ADV, handler_custom, local=False)
        # self.register_handler_adv(self.configuration.QUEUE_ADV, self._adv_message_handler, self.configuration.EXCHANGE)
        # start to handle messages
        self._messaging.start_consuming(connection_id)

    def consume_user_req(self, handler_custom=None, local=True):
        # connect
        connection_id = self._messaging.connect()

        self.register_handler_adv(connection_id, self.configuration.QUEUE_USER_REQ, handler_custom, local=True)
        # self.register_handler_adv(self.configuration.QUEUE_USER_REQ, self._adv_message_handler, '')
        # start to handle messages
        self._messaging.start_consuming(connection_id)

    def start_consume_adv(self):
        thread = Thread(name='ThreadConsumeAdv', target=self.consume_adv, args=())
        thread.start()
        thread.join()
