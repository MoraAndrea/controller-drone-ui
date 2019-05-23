import inspect
import json
import logging
import os
import socket
import threading
from os import path
from time import sleep

import psutil

from controller.Utils import vlc_yamlManager, parse_json
from controller.Utils.messaging import adv_messaging
from controller.Utils.messaging.ClassForMessageADV.advertisement_message import AdvMessage
from controller.Utils.messaging.ClassForMessageADV.appComponent import Component
from controller.Utils.messaging.ClassForMessageADV.componentResource import Resource
from controller.Utils.messaging.CommunicationDockerKubernetes.KubernetesManagerClass import KubernetesClass
from controller.Utils.messaging.result_messaging import Messaging_result
from controller.config.config import Configuration

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s', )

# NOT USED
def dragonOrchestrator(cv):
    try:
        logging.debug('Dragon thread started ...')
        with cv:
            # create resultfile
            logging.debug('Making resource available')

            # dragon

            logging.debug('Notifying to all')
            cv.notifyAll()
    except Exception as e:
        print("Exception --> " + str(e.status) + " " + str(e.reason))

# NOT USED
def deployTask(kubernetes, cv, yamlName):
    try:
        logging.debug('Deploy thread started ...')
        with cv:
            logging.debug('Result waiting ...')
            # cv.wait()
            logging.debug('Deploy task in result file')
            # run deploy ecc
            podName = kubernetes.create_pod(yamlName, "test")

    except Exception as e:
        print("Exception --> " + str(e.status) + " " + str(e.reason))


def runKube(classA, fileRequest, app, parameter, path):
    logger = classA.getLogger()
    if fileRequest is not None:
        if (check_possibility(fileRequest=fileRequest.name) is True):
            logger.submit_message('INFO', "Application describe in file " + fileRequest.name + " is run locally")
            print("Application describe in file " + fileRequest.name + " is run locally")
            message = AdvMessage()
            message.from_json(fileRequest.name)
            # run local
            return runKubeImpl_local(message)
        else:
            # this node cannot run the entire application so send request
            print("Send request for application describe in file: " + fileRequest.name)
            logger.submit_message('INFO', "Application describe in file " + fileRequest.name + " is run locally")
            adv_messaging.send_from_file_adv(fileRequest.name)  # send message adv to other nodes for drone orchestration

            # TODO: Dove aspetto il risultato di drone?
            messaging_res=Messaging_result()
            messaging_res.start_consume_result()

            message = AdvMessage()
            message.from_json(fileRequest.name)
            # run using drone result
            return runKubeImpl_distribuitedPods(message)

            # runKubeExample()
    else:
        if app and parameter is not None:
            message = create_json_with_request(app, parameter, socket.gethostname(), path)
            app_adv_messaging_OLD.send_adv(message)  # send message adv to other nodes for drone orchestration
            if (check_possibility(messageReq=message) is True):
                # run local
                pod=runKubeImpl_local(message)
                if pod is not False:
                    logger.submit_message('INFO', "Application is run locally")
                    print("Application is run locally")
                    return pod
                else:
                    return False
            else:
                # this node cannot run the entire application so send request
                logger.submit_message('INFO', "Send request for application: " + message.ID)
                print("Send request for application: " + message.ID)
                app_adv_messaging_OLD.send_adv(message)  # send message adv to other nodes for drone orchestration

                # TODO: Dove aspetto il risultato di drone?
                # run using drone result
                return runKubeImpl_distribuitedPods(message)

                # runKubeExample()
        else:
            return None


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


def runKubeImpl_distribuitedPods(message):
    podsRun = []
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

    # TODO: da cambiare quando si ha una soluzione effettiva di drone... fare come per message!!
    result = parse_json.parse_json_file(path.join(path.dirname(__file__), configuration.RESULT))
    print(result)

    order_services = []
    node_services = []
    for app in result:
        order_services = result[app]
        for service in result[app]:
            if service[2] == node_name:
                node_services.append(service)

    # node_services contiene i servizi da deployare su questo nodo: [0] image, [1] name, [2] node, [3] priority
    print(node_services)

    def sortKey(val):
        return val[3]

    order_services.sort(key=sortKey)
    # order_services ci sono i servizi ordinati in base a come devono essere deployati
    print(order_services)

    # run pod for streaming
    podStreamer_info = kubernetes.create_pod(
        path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-streamer.yaml"),
        configuration.NAMESPACE)
    podsRun.append(podStreamer_info)

    # i task devono essere deployati in ordine. controllo se ci sono
    if len(node_services) != 0:  # se ho qualcosa da eseguire controllo se quelli prima di me hanno fatto
        podStreamer_info = None
        priority = node_services[0][3]
        for i in range(1, priority):
            podStreamer_info = kubernetes.get_pod_info(order_services[0][1])
            while podStreamer_info.status.pod_ip == None:
                sleep(1)
                podStreamer_info = kubernetes.get_pod_info(order_services[0][1])
            print(podStreamer_info.status.pod_ip)

        # creo yaml con ip giusto
        nameNewFile = vlc_yamlManager.modifiedIp_vlcGUI(
            path.join(path.dirname(__file__), configuration.YAML_FOLDER + node_services[0][1] + ".yaml"),
            podStreamer_info.status.pod_ip)

        podGui_info = kubernetes.create_pod(
            path.join(path.dirname(__file__), nameNewFile),
            configuration.NAMESPACE)
        podsRun.append(podGui_info)
    return podsRun

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

    if memoryRequired < available and cpuRequred < psutil.cpu_count() and 1 == 1:
        return True
    else:
        return False


def runKubeExample():
    app_possible = ['VLC']

    configuration = Configuration("config/config.ini")
    kubernetes = KubernetesClass()

    # Definizione della condition variable per il file
    global request
    cv = threading.Condition()

    node_name = socket.gethostname()
    print(node_name + " " + socket.gethostbyname(node_name))
    # Risorse direttamente da os
    # print(psutil.cpu_percent())
    # print(psutil.cpu_count())
    # print(psutil.virtual_memory())
    # print(Utils.memory())
    # print(Utils.memory()['free'])

    # check exist namespaces and create this
    namespace = kubernetes.get_namespace(configuration.NAMESPACE)
    if namespace == None or namespace.status.phase != "Active":
        kubernetes.create_namespace(configuration.NAMESPACE)

    base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])) \
        .rpartition('/')[0]
    if os.path.isfile(path.join(path.dirname(__file__), configuration.REQUEST)):
        # Arriva la richiesta dell'utente la parsifico e decido cosa fare
        request = parse_json.parse_json_file(path.join(path.dirname(__file__), configuration.REQUEST))
        print("Request:")
        print(request)
        # if next(iter(request)) not in app_possible:
        #     print("ERROR: Sorry app not yet possible...")
        #     exit(1)
    else:
        print("no file")
        exit(1)

    # Posso eseguire tutta l'app?
    # calcolo totale delle risorse necessarie ecc
    memoryRequired = 0
    cpuRequred = 0
    app = next(iter(request))
    for service in request[app]:
        memoryRequired += request[app][service]['resources']['memory']
        cpuRequred += request[app][service]['resources']['cpu']

    values = psutil.virtual_memory()
    available = values.available >> 20  # display in MB format
    if memoryRequired < available and cpuRequred < psutil.cpu_count() and 1 == 2:
        # posso eseguire tutto
        podNameVideoLocal = kubernetes.create_pod(
            path.join(path.dirname(__file__), configuration.YAML_FOLDER + "video-gui-local-video.yaml"),
            configuration.NAMESPACE)
        return podNameVideoLocal
    else:
        # non posso eseguire tutto io: creo il problema in dragon --> Avvertisement

        # parte dragon --> soluzione (so cosa deve deployare ogni nodo)
        # threadDragon = threading.Thread(name='ThreadDragon', target=dragonOrchestrator, args=(cv,))
        # threadDragon.start()
        # threadDragon.join()

        result = parse_json.parse_json_file(path.join(path.dirname(__file__), configuration.RESULT))
        print(result)

        order_services = []
        node_services = []
        for app in result:
            order_services = result[app]
            for service in result[app]:
                if service[2] == node_name:
                    node_services.append(service)

        # node_services contiene i servizi da deployare su questo nodo: [0] image, [1] name, [2] node
        print(node_services)

        def sortKey(val):
            return val[3]

        order_services.sort(key=sortKey)
        # order_services ci sono i servizi ordinati in base a come devono essere deployati
        print(order_services)

        threadDeploy = threading.Thread(name='ThreadDeploy1', target=deployTask, args=(
            kubernetes, cv, path.join(path.dirname(__file__), "YamlFiles/video-streamer.yaml")))
        threadDeploy.start()
        threadDeploy.join()

        # i task devono essere deployati in ordine. controllo se ci sono
        if len(node_services) != 0:  # se ho qualcosa da eseguire controllo se quelli prima di me hanno fatto
            podStreamer_info = None
            priority = node_services[0][3]
            for i in range(1, priority):
                podStreamer_info = kubernetes.get_pod_info(order_services[0][1])
                while podStreamer_info.status.pod_ip == None:
                    sleep(1)
                    podStreamer_info = kubernetes.get_pod_info(order_services[0][1])
                print(podStreamer_info.status.pod_ip)

            # creo yaml con ip giusto
            nameNewFile = vlc_yamlManager.modifiedIp_vlcGUI(
                path.join(path.dirname(__file__), configuration.YAML_FOLDER + node_services[0][1] + ".yaml"),
                podStreamer_info.status.pod_ip)
            # faccio
            threadDeploy = threading.Thread(name='ThreadDeploy', target=deployTask,
                                            args=(kubernetes, cv, path.join(path.dirname(__file__), nameNewFile)))
            threadDeploy.start()
            threadDeploy.join()

        return ["video-gui", "video-streamer"]


def create_json_with_request(app, parameters, hostname, path):
    id = app
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

        message = AdvMessage(ID=id, owner=owner, components=components)
        with open('message_ADV.json', 'w') as fp:
            json.dump(message.to_dict(), fp, indent=4)

        return message
    else:
        return "not implemented"


def create_request(app, parameters, hostname, path):
    id = app
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

        message = AdvMessage(ID=id, owner=owner, components=components)

        return message
    else:
        return "not implemented"
