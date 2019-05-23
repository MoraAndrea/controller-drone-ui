from os import path
from threading import Thread

from controller.Utils.messaging.ClassForMessageResult.result_message import resultMessage
from controller.Utils.messaging.result_messaging import Messaging_result


def main():
    # connect
    #messaging_result.messaging.connect()
    #messaging_result.messaging.connect_write()
    #
    # # create exchange for federation
    # exchange_name = 'drone_exchange'
    # messaging.messaging.create_exchange(exchange=exchange_name, exchange_type='direct')

    message=resultMessage()
    message.from_json(path.join(path.dirname(__file__),"Result/result_drone.json"))

    messaging_result.send_result(message)
    #messaging.messaging.send_message("offloading-nodex", message,exchange_name)

def consume():
    # connect
    connection=messaging_result._messaging.connect()

    # create exchange for federation
    exchange_name = 'drone_exchange'
    messaging_result._messaging.create_exchange(exchange=exchange_name, exchange_type='direct')

    messaging_result.register_handler_result(connection,"offloading-nodex", messaging_result._result_message_handler, exchange_name)
    # start to handle messages
    messaging_result._messaging.start_consuming(connection)


if __name__ == '__main__':
    # init messaging
    messaging_result = Messaging_result("localhost")

    main()
    messaging_result.start_consume_result()
    # thread = Thread(target=consume)
    # thread.start()
    # thread.join()
