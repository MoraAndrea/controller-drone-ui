from os import path
from queue import Queue
from threading import Thread
from time import sleep

import yaml

from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.type import Type
from controller.Utils.messaging.ClassForMessageResult.result_message import resultMessage
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.adv_messaging import Messaging_adv
from controller.Utils.messaging.result_messaging import Messaging_result
from controller.config.config import Configuration

ADV_QUEUE = dict()


def test_produce():

    # for test:
    message = AdvMessage()
    message.from_json(path.join(path.dirname(__file__), configuration.REQUEST))
    messaging_adv.send_user_req(message, local=True)

    sleep(5)

    message_res = resultMessage()
    message_res.from_json(path.join(path.dirname(__file__), configuration.RESULT))
    messaging_result.send_result(message_res, local=True)


def dequeue_result(input_queue):
    while True:
        # retrieve data (blocking)
        result_message = input_queue.get(block=True, timeout=None)

        # do something with the result_message --> run your own components
        for component in result_message.components:
            print("-------> component " + component['name'] + " app " + component['app_name'])

            # for each component run deploy
            deployThread = Thread(target=deploy_component1, args=(component,))
            deployThread.start()

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
            print("-------> adv add: " + adv_message.app_name)
            ADV_QUEUE[adv_message.app_name] = adv_message  # add to adv dict

        # indicate data has been consumed
        input_queue.task_done()


def dequeue_user_request(input_queue):
    # this function was made because the user request can be different from the adv_message
    while True:
        # retrieve data (blocking)
        req_message = input_queue.get()

        # do something with the req --> save and send or delete
        if req_message.type == Type.DELETE:
            print("-------> delete: " + req_message.app_name)
            try:
                # ADV_QUEUE.pop(req_message.app_name)     # remove adv message. NOT USES BECAUSE DEQUEUE_ADV RECEIVE MESSAGE ADV
                messaging_adv.send_adv(req_message, local=False)
            except KeyError:
                print("Key not found")

        if req_message.type == Type.ADD:
            print("-------> user add: " + req_message.app_name)
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

    test_produce()


def deploy_component1(component):
    kubernetes = KubernetesClass()

    # search app_name in ADV_QUEUE for read info and parameters
    adv_app = ADV_QUEUE[component['app_name']]
    adv_app_component = None  # component with all information
    for c in adv_app.components:
        if c['name'] == component['name']:
            adv_app_component = c
            break

    name_yaml = adv_app_component['name']
    print(name_yaml)
    # open default yaml document
    with open(configuration.YAML_FOLDER + name_yaml + ".yaml") as f:
        obj_yaml = yaml.safe_load(f)

    if 'service' in adv_app_component['parameters']:
        service=kubernetes.create_service_object(obj_yaml['metadata']['name'])
        kubernetes.create_generally('Service', service)

    if obj_yaml['kind'] == "Pod":
        yaml_new = modified_default_yaml_pod(adv_app_component)
    else:
        yaml_new = modified_default_yaml_deployment(adv_app_component)

    kubernetes.create_generally(obj_yaml['kind'],yaml_new)

def deploy_component(component):
    kubernetes = KubernetesClass()

    # search app_name in ADV_QUEUE for read info and parameters
    adv_app = ADV_QUEUE[component['app_name']]
    adv_app_component = None  # component with all information
    for c in adv_app.components:
        if c['name'] == component['name']:
            adv_app_component = c
            break


    # check if dependencies are running
    boot_dependencies=adv_app_component['boot_dependencies']
    podStreamer_info=None
    for dep in boot_dependencies:
        while podStreamer_info == None:
            podStreamer_info = kubernetes.get_pod_info(dep)
            sleep(1)
        while podStreamer_info.status.pod_ip == None:
            sleep(1)
            podStreamer_info = kubernetes.get_pod_info(dep)
            print(podStreamer_info.status.pod_ip)

    print()

    # from component name chose right yaml
    # read parameters and function from adv_app_component for deploy
    if 'ip' in adv_app_component['parameters']:
        adv_app_component['parameters']['ip'] = podStreamer_info.status.pod_ip
    yaml = modified_default_yaml_pod(adv_app_component)

    pod_info = kubernetes.create_pod(yaml, configuration.NAMESPACE)

# TODO: da fare meglio!!!
def modified_default_yaml_pod(adv_app_component):
    name_yaml=adv_app_component['name']
    print(name_yaml)
    # open default yaml document
    with open(configuration.YAML_FOLDER + name_yaml + ".yaml") as f:
        def_yaml = yaml.safe_load(f)

    # edit fields
    # def_yaml['spec']['nodeName']=socket.gethostname()
    def_yaml['spec']['containers'][0]['resources']['requests'] = adv_app_component['function']['resources']
    def_yaml['spec']['containers'][0]['resources']['limits'] = adv_app_component['function']['resources']
    if adv_app_component['parameters'] is not None:
        for param_type in adv_app_component['parameters']:
            def_yaml['spec']['containers'][0]['args'][0] = def_yaml['spec']['containers'][0]['args'][0].replace(
                '{' + param_type + '}', adv_app_component['parameters'][param_type])

    return def_yaml

# TODO: da fare meglio!!!
def modified_default_yaml_deployment(adv_app_component):
    name_yaml=adv_app_component['name']
    print(name_yaml)
    # open default yaml document
    with open(configuration.YAML_FOLDER + name_yaml + ".yaml") as f:
        def_yaml = yaml.safe_load(f)

    # edit fields
    # def_yaml['spec']['nodeName']=socket.gethostname()
    def_yaml['spec']['template']['spec']['containers'][0]['resources']['requests'] = adv_app_component['function'][
        'resources']
    def_yaml['spec']['template']['spec']['containers'][0]['resources']['limits'] = adv_app_component['function'][
        'resources']
    if adv_app_component['parameters'] is not None:
        for param_type in adv_app_component['parameters']:
            def_yaml['spec']['template']['spec']['containers'][0]['args'][0] = \
            def_yaml['spec']['template']['spec']['containers'][0]['args'][0].replace(
                '{' + param_type + '}', str(adv_app_component['parameters'][param_type]))

    return def_yaml

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
