import socket
from os import path
from queue import Queue
from threading import Thread
from time import sleep

from controller.Utils import vlc_yamlManager
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageResult.result_message import resultMessage
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.adv_messaging import Messaging_adv
from controller.Utils.messaging.result_messaging import Messaging_result
from controller.config.config import Configuration

def test_produce(output_queue):
    while True:
        output_queue.put("test")

def dequeue_result(input_queue):
    while True:
        # retrieve data (blocking)
        result_message = input_queue.get(block=True, timeout=None)

        # do something with the result_message --> run your own components
        print("-------> "+result_message.ID)
        deployThread = Thread(target=deploy_components,args=(result_message,))
        deployThread.start()

        # indicate data has been consumed
        input_queue.task_done()

def dequeue_adv(input_queue):
    while True:
        # retrieve data (blocking)
        adv_message = input_queue.get(block=True, timeout=None)

        # do something with the adv --> save or delete
        if adv_message.type=="del":
            print("-------> delete: "+adv_message.ID)

        if adv_message.type=="add":
            print("-------> add: "+adv_message.ID)

        # indicate data has been consumed
        input_queue.task_done()

def run_controller():
    # configuration
    configuration = Configuration("config/config.ini")

    #init queue
    shared_queue_res = Queue()
    shared_queue_adv = Queue()

    # init messaging
    messaging_result = Messaging_result("localhost", shared_queue_res)
    messaging_adv = Messaging_adv("localhost", shared_queue_adv)

    # thread that wait result
    t1 = Thread(target=dequeue_result, args=(shared_queue_res,))
    # thread that wait adv
    t2 = Thread(target=dequeue_adv, args=(shared_queue_adv,))

    # thread that consume result message from rabbit
    t3 = Thread(name='ThreadConsumeResult', target=messaging_result.consume_result, args=(messaging_result._result_message_handler_enqueue,))
    # thread that consume adv message from rabbit
    t4 = Thread(name='ThreadConsumeAdv', target=messaging_adv.consume_adv,args=(messaging_adv._adv_message_handler_enqueue,))

    t1.start()
    t2.start()
    t3.start()
    t4.start()

    # for test:
    message = AdvMessage()
    message.from_json(path.join(path.dirname(__file__), configuration.REQUEST))
    messaging_adv.send_adv(message)

    message_res = resultMessage()
    message_res.from_json(path.join(path.dirname(__file__), configuration.RESULT))
    messaging_result.send_result(message)

def deploy_components(result_message=None):
    if result_message is not None:
        configuration = Configuration("config/config.ini")
        kubernetes = KubernetesClass()
        podsRun=[]

        # get hostname
        node_name = socket.gethostname()
        print(node_name + " " + socket.gethostbyname(node_name))

        # check exist namespaces and create this
        namespace = kubernetes.get_namespace(configuration.NAMESPACE)
        if namespace == None or namespace.status.phase != "Active":
            kubernetes.create_namespace(configuration.NAMESPACE)

        # TODO: fare in modo che cambia il file video nello yaml leggendo in result_message o adv_message

        order_services = []
        node_services = []
        for component in result_message.components:
            order_services.append(component)
            if component['winner'] == node_name:
                node_services.append(component)

        # node_services contains only the components to be run on this node: name, image, winnerNode, priority
        print(node_services)
        node_services = sorted(node_services, key=lambda k: k['priority'])

        # order_services contains components sorted by priority
        order_services = sorted(order_services, key=lambda k: k['priority'])
        #order_services = sorted(order_services, key=operator.itemgetter('priority'), reverse=True)
        print(order_services)

        # TODO: migliorare il controllo della priority --> generalizzare o farlo solo per vlc??
        # check if this node must run a component
        if len(node_services) != 0:
            priority = node_services[0]['priority'] # priority of this node component

            if node_services[0]['name'] == 'video-streamer':
                podStreamer_info = kubernetes.create_pod(
                    path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-streamer.yaml"),
                    configuration.NAMESPACE)
                podsRun.append(podStreamer_info)

            for i in range(1, priority):    # then check if components with highest priority is run if exist
                podStreamer_info = kubernetes.get_pod_info(order_services[0]['name'])
                if podStreamer_info is not None:
                    while podStreamer_info.status.pod_ip == None:
                        sleep(1)
                        podStreamer_info = kubernetes.get_pod_info(order_services[0]['name'])
                    print(podStreamer_info.status.pod_ip)

                    if node_services[0]['name']=='video-gui':
                        # creo yaml con ip giusto
                        nameNewFile = vlc_yamlManager.modifiedIp_vlcGUI(
                        path.join(path.dirname(__file__), configuration.YAML_FOLDER + node_services[0]['name'] + ".yaml"),
                            podStreamer_info.status.pod_ip)

                        podGui_info = kubernetes.create_pod(path.join(path.dirname(__file__), nameNewFile),configuration.NAMESPACE)
                        podsRun.append(podGui_info)
        return podsRun

if __name__ == '__main__':
    run_controller()

