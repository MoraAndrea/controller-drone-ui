import socket
from os import path
from queue import Queue
from threading import Thread
from time import sleep

import yaml

from controller.Utils import vlc_yamlManager
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.type import Type
from controller.Utils.messaging.ClassForMessageResult.result_message import resultMessage
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.adv_messaging import Messaging_adv
from controller.Utils.messaging.result_messaging import Messaging_result
from controller.config.config import Configuration

ADV_QUEUE = dict()


def test_produce(output_queue):
    while True:
        output_queue.put("test")


def dequeue_result(input_queue):
    while True:
        # retrieve data (blocking)
        result_message = input_queue.get(block=True, timeout=None)

        # do something with the result_message --> run your own components
        for component in result_message.components:
            print("-------> component " + component['name'] + " app " + component['app_name'])

            # run single component
            deployThread = Thread(target=deploy_component, args=(component,))
            deployThread.start()

        # deployThread = Thread(target=deploy_components, args=(result_message,))
        # deployThread.start()

        # indicate data has been consumed
        input_queue.task_done()


def dequeue_adv(input_queue):
    while True:
        # retrieve data (blocking)
        adv_message = input_queue.get(block=True, timeout=None)

        # do something with the adv --> save or delete
        if adv_message.type == Type.DELETE:
            print("-------> delete: " + adv_message.app_name)
            # TODO: check if this node has component of this app, so deleted
            try:
                ADV_QUEUE.pop(adv_message.app_name)  # remove adv message
            except KeyError:
                print("Key not found")

        if adv_message.type == Type.ADD:
            print("-------> add: " + adv_message.app_name)
            ADV_QUEUE[adv_message.app_name] = adv_message  # add to adv dict

        # indicate data has been consumed
        input_queue.task_done()


def dequeue_user_request(input_queue):
    # this function was made because the user request can be different from the adv_message
    while True:
        # retrieve data (blocking)
        req_message = input_queue.get(block=True, timeout=None)

        # do something with the req --> save and send or delete
        if req_message.type == Type.DELETE:
            print("-------> delete: " + req_message.app_name)
            try:
                # ADV_QUEUE.pop(req_message.app_name)     # remove adv message. NOT USES BECAUSE DEQUEUE_ADV RECEIVE MESSAGE ADV
                messaging_adv.send_adv(req_message, local=False)
            except KeyError:
                print("Key not found")

        if req_message.type == Type.ADD:
            print("-------> add: " + req_message.app_name)
            # ADV_QUEUE[req_message.app_name]=req_message     # save req message. NOT USES BECAUSE DEQUEUE_ADV RECEIVE MESSAGE ADV
            # send to other nodes
            messaging_adv.send_adv(req_message, local=False)  # send adv to other nodes

        # indicate data has been consumed
        input_queue.task_done()


def run_controller():
    # thread that wait result
    t1 = Thread(target=dequeue_result, args=(shared_queue_res,))
    # thread that wait adv
    t2 = Thread(target=dequeue_adv, args=(shared_queue_adv,))
    # thread that wait user req
    t3 = Thread(target=dequeue_user_request, args=(shared_queue_user_req,))

    # thread that consume result message from rabbit
    t4 = Thread(name='ThreadConsumeResult', target=messaging_result.consume_result,
                args=(messaging_result._result_message_handler_enqueue,))
    # thread that consume adv message from rabbit
    t5 = Thread(name='ThreadConsumeAdv', target=messaging_adv.consume_adv,
                args=(messaging_adv._adv_message_handler_enqueue,))
    # thread that consume user request message from rabbit
    t6 = Thread(name='ThreadConsumeUserReq', target=messaging_adv.consume_user_req,
                args=(messaging_adv._user_req_message_handler_enqueue,))

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()

    # for test:
    message = AdvMessage()
    message.from_json(path.join(path.dirname(__file__), configuration.REQUEST))
    messaging_adv.send_user_req(message, local=True)

    sleep(3)

    message_res = resultMessage()
    message_res.from_json(path.join(path.dirname(__file__), configuration.RESULT))
    messaging_result.send_result(message_res, local=True)

def deploy_component(component):
    # search app_name in ADV_QUEUE for read info and parameters
    adv_app = ADV_QUEUE[component['app_name']]
    adv_app_component = None  # component with all information
    for c in adv_app.components:
        if c['name'] == component['name']:
            adv_app_component = c
            break

    # from component name chose right yaml
    # read parameters and function from adv_app_component for deploy
    modified_default_yaml(adv_app_component)

    print()

# TODO: da fare meglio!!!
def modified_default_yaml(adv_app_component):
    # open default yaml document
    with open(path.join(path.dirname(__file__),
                        configuration.YAML_FOLDER + adv_app_component['name'] + ".yaml")) as f:
        def_yaml = yaml.safe_load(f)

    # edit fields
    def_yaml['spec']['nodeName']=socket.gethostname()
    def_yaml['spec']['containers'][0]['resources']['requests'] = adv_app_component['function']['resources']
    def_yaml['spec']['containers'][0]['resources']['limits']=adv_app_component['function']['resources']
    if adv_app_component['parameters'] is not None:
        for param_type in adv_app_component['parameters']:
            str=def_yaml['spec']['containers'][0]['args'][0].replace('{'+param_type+'}',adv_app_component['parameters'][param_type])
            def_yaml['spec']['containers'][0]['args'][0]=str

    print( def_yaml['spec']['containers'][0]['args'][0])

    kubernetes = KubernetesClass()
    kubernetes.create_generic(def_yaml)
    print()

def deploy_components(result_message=None):
    if result_message is not None:
        configuration = Configuration("config/config.ini")
        kubernetes = KubernetesClass()
        podsRun = []

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
        # order_services = sorted(order_services, key=operator.itemgetter('priority'), reverse=True)
        print(order_services)

        # TODO: migliorare il controllo della priority --> generalizzare o farlo solo per vlc??
        # check if this node must run a component
        if len(node_services) != 0:
            priority = node_services[0]['priority']  # priority of this node component

            if node_services[0]['name'] == 'video-streamer':
                podStreamer_info = kubernetes.create_pod(
                    path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-streamer.yaml"),
                    configuration.NAMESPACE)
                podsRun.append(podStreamer_info)

            for i in range(1, priority):  # then check if components with highest priority is run if exist
                podStreamer_info = kubernetes.get_pod_info(order_services[0]['name'])
                if podStreamer_info is not None:
                    while podStreamer_info.status.pod_ip == None:
                        sleep(1)
                        podStreamer_info = kubernetes.get_pod_info(order_services[0]['name'])
                    print(podStreamer_info.status.pod_ip)

                    if node_services[0]['name'] == 'video-gui':
                        # creo yaml con ip giusto
                        nameNewFile = vlc_yamlManager.modifiedIp_vlcGUI(
                            path.join(path.dirname(__file__),
                                      configuration.YAML_FOLDER + node_services[0]['name'] + ".yaml"),
                            podStreamer_info.status.pod_ip)

                        podGui_info = kubernetes.create_pod(path.join(path.dirname(__file__), nameNewFile),
                                                            configuration.NAMESPACE)
                        podsRun.append(podGui_info)
        return podsRun


if __name__ == '__main__':
    # configuration
    configuration = Configuration("config/config.ini")

    # init queue
    shared_queue_res = Queue()
    shared_queue_adv = Queue()
    shared_queue_user_req = Queue()

    # init messaging
    messaging_result = Messaging_result("localhost", shared_queue_res)
    messaging_adv = Messaging_adv("localhost", shared_queue_adv, shared_queue_user_req)

    run_controller()
