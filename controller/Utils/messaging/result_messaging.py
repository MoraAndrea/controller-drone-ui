import json
from threading import Thread

from controller.Utils import singleton
from controller.Utils.messaging.ClassForMessageResult.result_message import resultMessage
from controller.Utils.messaging.messaging import Messaging
from controller.config.config import Configuration


class Messaging_result(object, metaclass=singleton.Singleton):

    def __init__(self, broker=None,queue=None):
        # init messaging
        self._messaging = Messaging(broker)
        self._message_handler = None
        self.configuration = Configuration("config/config.ini")
        self.output_queue = queue   # queue for read result message

    def register_handler_result(self,connection_id, topic, handler, exchange_name):
        if connection_id not in self._messaging._channels:
            print(connection_id+" not found")
        self._messaging._channels[connection_id].queue_declare(queue=topic)
        self._messaging._channels[connection_id].queue_bind(exchange=exchange_name, queue=topic)
        if handler is None:
            handler = self._result_message_handler
        self._message_handler = handler
        self._messaging._channels[connection_id].basic_consume(
            self._message_callback_result, queue=topic, no_ack=True)

    @staticmethod
    def _message_callback_result(ch, method, properties, body):
        print(" [x] Received " + body.decode())
        self = Messaging_result()
        message = resultMessage()
        message.parse_dict(json.loads(body.decode()))
        self._message_handler(message)

    @staticmethod
    def _result_message_handler(message):
        print("Received result for app " + message.ID)

    def _result_message_handler_enqueue(self,message):
        print("Received result for app " + message.ID)
        self.output_queue.put(message)

    def send_from_file_result(self, file,local=False):
        connection_id=self._messaging.connect()

        if local:
            exchange = ''
        else:
            exchange = self.configuration.EXCHANGE

        message = resultMessage()
        message.from_json(file)

        self._messaging.send_message(connection_id,self.configuration.QUEUE_RESULT, message, exchange)

        self._messaging.disconnect(connection_id)

    def send_result(self, message,local=False):
        connection_id=self._messaging.connect()

        if local:
            exchange = ''
        else:
            exchange = self.configuration.EXCHANGE

        self._messaging.send_message(connection_id,self.configuration.QUEUE_RESULT, message, exchange)

        self._messaging.disconnect(connection_id)

    def consume_result(self, handler_custom=None):
        connection_id=self._messaging.connect()

        self.register_handler_result(connection_id,self.configuration.QUEUE_RESULT, handler_custom, self.configuration.EXCHANGE)
        # self.register_handler_result(self.configuration.QUEUE_RESULT, self._result_message_handler,self.configuration.EXCHANGE)

        # start to handle messages
        self._messaging.start_consuming(connection_id)

    def start_consume_result(self):
        thread = Thread(name='ThreadConsumeRes', target=self.consume_result,args=())
        thread.start()
        thread.join()
