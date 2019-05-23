import json
import os
import socket
from os import path

import psutil

from controller.Utils import vlc_yamlManager
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.appComponent import Component
from controller.Utils.messaging.ClassForMessageADV.componentResource import Resource
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.adv_messaging import Messaging_adv
from controller.config.config import Configuration

def send_request_app(classLogger, fileRequest, app, parameter, path=None):
    logger = classLogger.getLogger()
    messaging_adv=Messaging_adv("localhost")
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
            messaging_adv.send_from_file_adv(fileRequest.name,local=True)  # send message to controller
            return True
    else:
        if app and parameter is not None:
            message = create_request(app,"add", parameter, socket.gethostname(), path)
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
                logger.submit_message('INFO', "Send request for application: " + message.ID)
                print("Send request for application: " + message.ID)
                messaging_adv.send_adv(message,local=True)   # send message to controller
                return True
        else:
            return None

def send_del_message_to_rabbit(classA, fileRequest, app, parameter):
    logger = classA.getLogger()
    messaging_adv=Messaging_adv("localhost")
    if fileRequest is not None:
        message = AdvMessage()
        message.from_json(fileRequest.name)
        message_del = create_request(app,'del', parameter, socket.gethostname(), path)
        messaging_adv.send_adv(message_del)
        logger.submit_message('INFO', "Send request for delete application describe in file: " + fileRequest.name)
    else:
        message = create_request(app,'del', parameter, socket.gethostname(), path)
        messaging_adv.send_adv(message)
        logger.submit_message('INFO', "Send request for delete application: " + message.ID)


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

    fileNameMod=vlc_yamlManager.modified_localVideo(path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-gui-local-video.yaml"), message.components[1]['parameter'])

    # local run pod
    #podNameVideoLocal = kubernetes.create_pod(path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-gui-local-video.yaml"),configuration.NAMESPACE)

    podNameVideoLocal = kubernetes.create_pod(path.join(path.dirname(__file__), fileNameMod),configuration.NAMESPACE)
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

def create_json_with_request(app,type, parameters, hostname, path):
    id = app
    type =type
    if id == 'VLC':
        owner = hostname
        components = []
        componentGUI = Component(name="video-gui", image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                                 priority="2", resources=Resource(memory=256, cpu=0.5).to_dict(),
                                 blacklist=["node2"], parameter=None)
        components.append(componentGUI.to_dict())
        componentStream = Component(name="video-streamer", image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                                    priority="1", resources=Resource(memory=1024, cpu=2).to_dict(),
                                    blacklist=["node2"], parameter=path)
        components.append(componentStream.to_dict())

        message = AdvMessage(ID=id, owner=owner, components=components, type=type)
        with open('message_ADV.json', 'w') as fp:
            json.dump(message.to_dict(), fp, indent=4)

        return message
    else:
        return "not implemented"


def create_request(app,type, parameters, hostname, path):
    id = app
    type =type
    if id == 'VLC':
        owner = hostname
        components = []
        componentGUI = Component(name="video-gui", image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                                 priority="2", resources=Resource(memory=256, cpu=0.5).to_dict(),
                                 blacklist=["node2"], parameter=None)
        components.append(componentGUI.to_dict())
        componentStream = Component(name="video-streamer", image="andreamora/imagerepo:vlcnoentrypointwithplugins",
                                    priority="1", resources=Resource(memory=1024, cpu=2).to_dict(),
                                    blacklist=["node2"], parameter=None)
        components.append(componentStream.to_dict())

        message = AdvMessage(ID=id, owner=owner, components=components,type=type)

        return message
    else:
        return "not implemented"
