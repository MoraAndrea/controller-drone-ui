from threading import Thread
import json
from os import path

from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.appComponent import Component
from controller.Utils.messaging.ClassForMessageADV.componentResource import Resource
from controller.Utils.messaging.adv_messaging import Messaging_adv


def main():
    message=create_json_with_request()

    # create exchange for federation
    # exchange_name = 'drone_exchange'
    # messaging.create_exchange(connection,exchange=exchange_name, exchange_type='direct')

    message=AdvMessage()
    message.from_json(path.join(path.dirname(__file__),"Request/advertisement.json"))

    messaging_adv.send_adv(message)

def consume():
    # connect
    connection = messaging_adv._messaging.connect()

    # create exchange for federation
    exchange_name = 'drone_exchange'
    messaging_adv._messaging.create_exchange(exchange=exchange_name, exchange_type='direct')

    messaging_adv.register_handler_adv(connection, "drone_adv", messaging_adv._adv_message_handler,
                                             exchange_name)
    # start to handle messages
    messaging_adv._messaging.start_consuming(connection)

def create_json_with_request():

    id="VLC"
    owner="node1"
    components=[]
    component1=Component("video","image:tag","1",resources=Resource(memory=256,cpu=0.5).to_dict(),blacklist=["node1"])
    components.append(component1.to_dict())
    component2=Component("stream","image:tag","2",resources=Resource(memory=1024,cpu=1).to_dict(),blacklist=["node1"])
    components.append(component2.to_dict())

    message = AdvMessage(ID=id,owner=owner,components=components)
    with open('mes.json', 'w') as fp:
        json.dump(message.to_dict(), fp,indent=4)

    return message

if __name__ == '__main__':
    # init messaging
    messaging_adv = Messaging_adv("localhost")

    main()
    thread = Thread(target=consume)
    thread.start()
    thread.join()