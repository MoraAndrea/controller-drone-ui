import json
import os
import socket
import uuid
from os import path

import psutil

from controller.Utils import vlc_yamlManager
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.appComponent import Component
from controller.Utils.messaging.ClassForMessageADV.componentFunction import Function
from controller.Utils.messaging.ClassForMessageADV.componentResource import Resource
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.adv_messaging import Messaging_adv
from controller.config.config import Configuration

APP_RUNNING=dict()

def send_request_app(classLogger, fileRequest, app, parameter, path=None):
    logger = classLogger.getLogger()
    messaging_adv = Messaging_adv("localhost")
    if fileRequest is not None:
        if (check_possibility(fileRequest=fileRequest.name) is True):
            # this node can run the entire application
            # TODO: vedere come farlo
            # logger.submit_message('INFO', "Application describe in file " + fileRequest.name + " is run locally")
            # print("Application describe in file " + fileRequest.name + " is run locally")
            # message = AdvMessage()
            # message.from_json(fileRequest.name)
            # # run local
            # return runKubeImpl_local(message)
            pass
        else:
            # this node cannot run the entire application so send request
            print("Send request for application describe in file: " + fileRequest.name)
            logger.submit_message('INFO', "Send request for application describe in file: " + fileRequest.name)

            request_message = AdvMessage()
            request_message.from_json(fileRequest.name)
            messaging_adv.send_user_req(request_message, local=True)  # send message to controller
            APP_RUNNING[request_message.app_name]=request_message
            return True
    else:
        if app and parameter is not None:
            message = create_request(app, "add", parameter, socket.gethostname(), path)
            if (check_possibility(messageReq=message) is True):
                # this node can run the entire application
                # TODO: vedere come farlo
                # pod=runKubeImpl_local(message)
                # if pod is not False:
                #     logger.submit_message('INFO', "Application is run locally")
                #     print("Application is run locally")
                #     return pod
                # else:
                #     return False
                pass
            else:
                # this node cannot run the entire application so send request
                print("Send request for application: " + message.app_name)
                logger.submit_message('INFO', "Send request for application: " + message.app_name)

                messaging_adv.send_user_req(message, local=True)  # send message to controller
                APP_RUNNING[message.app_name] = message
                return True
        else:
            return None

# pass filename of file or App_ID of deploy app
def send_delete_app(classLogger, fileRequest=None, app_id=None):
    logger = classLogger.getLogger()
    messaging_adv = Messaging_adv("localhost")
    if fileRequest is not None:
        message_del = AdvMessage()
        message_del.from_json(fileRequest.name)
        message_del.type='del'
        messaging_adv.send_user_req(message_del, local=True) # send message to controller
        try:
            APP_RUNNING.pop(message_del.app_name)  # remove app running
        except KeyError:
            print("Key not found")
        logger.submit_message('INFO', "Send request for delete application describe in file: " + fileRequest.name)
    else:
        app_del=APP_RUNNING[app_id]
        messaging_adv.send_user_req(app_del, local=True) # send message to controller
        try:
            APP_RUNNING.pop(app_del.app_name) # remove app running
        except KeyError:
            print("Key not found")
        logger.submit_message('INFO', "Send request for delete application: " + app_del.app_name)


def runKubeImpl_local(message):
    configuration = Configuration("config/config.ini")
    kubernetes = KubernetesClass()

    # get hostname
    node_name = socket.gethostname()
    print(node_name + " " + socket.gethostbyname(node_name))

    # check exist namespaces and create this
    namespace = kubernetes.get_namespace(configuration.NAMESPACE)
    if namespace == None or namespace.status.phase != "Active":
        kubernetes.create_namespace(configuration.NAMESPACE)

    # TODO: fare in modo che cambia il file video nello yaml leggendo in fileRequest

    fileNameMod = vlc_yamlManager.modified_localVideo(
        path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-gui-local-video.yaml"),
        message.components[1]['parameter'])

    # local run pod
    # podNameVideoLocal = kubernetes.create_pod(path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-gui-local-video.yaml"),configuration.NAMESPACE)

    podNameVideoLocal = kubernetes.create_pod(path.join(path.dirname(__file__), fileNameMod), configuration.NAMESPACE)
    return podNameVideoLocal


# check if this node can run all application
def check_possibility(fileRequest=None, messageReq=None):
    message = AdvMessage()
    if fileRequest is not None and os.path.isfile(fileRequest):
        message.from_json(fileRequest)
    else:
        if messageReq is not None:
            message = messageReq
        else:
            print("no file")
            exit(1)

    memoryRequired = 0
    cpuRequred = 0
    for component in message.components:
        memoryRequired += component['resources']['memory']
        cpuRequred += component['resources']['cpu']

    values = psutil.virtual_memory()
    available = values.available >> 20  # display in MB format

    if memoryRequired < available and cpuRequred < psutil.cpu_count() and 1 == 2:
        return True
    else:
        return False


def create_json_with_request(app, type, parameters, hostname, path):
    app_name = app + uuid.uuid4().hex[:6].upper()
    type = type
    if app == 'VLC':
        base_node = hostname
        components = []

        func = Function(image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                        resources=Resource(memory=256, cpu=0.5).to_dict())

        componentGUI = Component(name="video-gui", function=func.to_dict(),
                                 boot_dependencies=["2"], nodes_blacklist=["node2"], nodes_whitelist=["node2"],
                                 parameter=None)
        components.append(componentGUI.to_dict())
        componentStream = Component(name="video-streamer", function=func.to_dict(),
                                    boot_dependencies=["2"], nodes_blacklist=["node2"], nodes_whitelist=["node2"],
                                    parameter=path)
        components.append(componentStream.to_dict())

        message = AdvMessage(app_name=app_name, base_node=base_node, components=components, type=type)
        with open('message_ADV.json', 'w') as fp:
            json.dump(message.to_dict(), fp, indent=4)

        return message
    else:
        return "not implemented"


def create_request(app, type, parameters, hostname, path):
    app_name = app + uuid.uuid4().hex[:6].upper()
    type = type
    if app == 'VLC':
        base_node = hostname
        components = []

        func = Function(image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                        resources=Resource(memory=256, cpu=0.5).to_dict())

        componentGUI = Component(name="video-gui", function=func.to_dict(),
                                 boot_dependencies=["2"], nodes_blacklist=["node2"], nodes_whitelist=["node2"],
                                 parameter=None)
        components.append(componentGUI.to_dict())
        componentStream = Component(name="video-streamer", function=func.to_dict(),
                                    boot_dependencies=["2"], nodes_blacklist=["node2"], nodes_whitelist=["node2"],
                                    parameter=path)
        components.append(componentStream.to_dict())

        message = AdvMessage(app_name=app_name, base_node=base_node, components=components, type=type)
        return message
    else:
        return "not implemented"
