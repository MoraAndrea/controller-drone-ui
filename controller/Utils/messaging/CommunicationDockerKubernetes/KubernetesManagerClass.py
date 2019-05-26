import re

from kubernetes import client, config, stream
from os import path
import yaml

from controller.Utils import singleton


class KubernetesClass(object, metaclass=singleton.Singleton):
    """
    This class manage kubernetes communication
    """

    def __init__(self):
        config.load_kube_config()

    @staticmethod
    def create_namespace(namespace):
        k8s = client.CoreV1Api()
        try:
            k8s.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))
        except Exception as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))

    def create_deployment_object(self,name,image_container,container_port,name_deployment):
        # Configureate Pod template container
        container = client.V1Container(
            name=name,
            image=image_container,
            ports=[client.V1ContainerPort(container_port=container_port)])
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"run": name}),
            spec=client.V1PodSpec(containers=[container]))
        # Create and configurate a selection sector
        selector = client.V1LabelSelector(match_labels={"run":name})
        # Create the specification of deployment
        spec = client.ExtensionsV1beta1DeploymentSpec(
            template=template,
            selector=selector)
        # Instantiate the deployment object
        deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name_deployment),
            spec=spec)

        return deployment

    def create_service_object(self,name):
        k8s = client.CoreV1Api()

        body = client.V1Service()  # V1Service
        # Creating Meta Data
        metadata = client.V1ObjectMeta()
        metadata.name = name
        metadata.labels={"run": name}
        body.metadata = metadata

        # Creating spec
        spec = client.V1ServiceSpec()
        # Creating Port object
        port = client.V1ServicePort(port=8080)
        port.protocol = 'TCP'

        spec.ports = [port]
        spec.selector = {"run": name}

        body.spec = spec
        return body

    def create_generally(self, kind, yaml):
        if kind == 'Pod':
            return self.create_pod(yaml,"test")
        if kind == 'Deployment':
            return self.create_deployment(yaml,"test")
        if kind == 'Service':
            return self.create_service(yaml,"test")

    @staticmethod
    def create_pod_from_file(fileYaml, namespace):
        with open(path.join(path.dirname(__file__), fileYaml)) as f:
            pod = yaml.safe_load(f)
            k8s = client.CoreV1Api()
            try:
                resp = k8s.create_namespaced_pod(body=pod, namespace=namespace)
                print("Pod created.\n status='%s'" % str(resp.status))
                return pod['metadata']['name']
            except Exception as e:
                print("Exception --> " + str(e.status) + " " + str(e.reason))
                print('Failed to create Pod: ' + str(e))
                return False

    @staticmethod
    def create_pod(yaml, namespace):
        k8s = client.CoreV1Api()
        try:
            resp = k8s.create_namespaced_pod(body=yaml, namespace=namespace)
            print("Pod created.\n status='%s'" % str(resp.status))
            return yaml['metadata']['name']
        except Exception as e:
            if e.status != 409:
                return False
            try:
                print('Pod conflict: ' + str(e))
                k8s.patch_namespaced_pod(name=yaml['metadata']['name'],body=yaml, namespace=namespace)
            except Exception as e:
                try:
                    # second attempt... delete the existing object and re-insert
                    resp = k8s.delete_namespaced_pod(name=yaml['metadata']['name'],namespace=namespace)
                    resp = k8s.create_namespaced_pod(body=yaml, namespace=namespace)
                except Exception as e:
                    print("Exception --> " + str(e.status) + " " + str(e.reason))
                    print('Failed to create Pod: ' + str(e))
                    return False

    @staticmethod
    def create_deployment_from_file(fileYaml, namespace):
        with open(path.join(path.dirname(__file__), fileYaml)) as f:
            dep = yaml.safe_load(f)
            k8s = client.AppsV1Api()
            try:
                resp = k8s.create_namespaced_deployment(body=dep, namespace=namespace)
                print("Deployment created.\n status='%s'" % str(resp.status))
            except Exception as e:
                print("Exception --> " + str(e.status) + " " + str(e.reason))
                print('Failed to create Deployment: ' + str(e))

    @staticmethod
    def create_deployment(yaml, namespace):
        k8s = client.AppsV1Api()
        try:
            resp = k8s.create_namespaced_deployment(body=yaml, namespace=namespace)
            print("Deployment created.\n status='%s'" % str(resp.status))
        except Exception as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))
            print('Failed to create Deployment: ' + str(e))

    @staticmethod
    def create_service_from_file(fileyaml, namespace):
        with open(path.join(path.dirname(__file__), fileyaml)) as f:
            service = yaml.safe_load(f)
            k8s = client.CoreV1Api()
            try:
                resp = k8s.create_namespaced_service(body=service, namespace=namespace)
                print("Service created.\n status='%s'" % str(resp.status))
            except Exception as e:
                print("Exception --> " + str(e.status) + " " + str(e.reason))
                print('Failed to create Service: ' + str(e))

    @staticmethod
    def create_service(yaml, namespace):
        k8s = client.CoreV1Api()
        try:
            resp = k8s.create_namespaced_service(body=yaml, namespace=namespace)
            print("Service created.\n status='%s'" % str(resp.status))
        except client.ExtensionsApi as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))
            print('Failed to create Service: ' + str(e))

    @staticmethod
    def delete_pod_in_yaml(fileYaml, namespace):
        with open(path.join(path.dirname(__file__), fileYaml)) as f:
            dep = yaml.safe_load(f)
            k8s = client.CoreV1Api()
            k8s.list_node()
            try:
                resp = k8s.delete_namespaced_pod(name=str(dep['metadata']['name']), namespace=namespace)
                print("Pod deleted. status='%s'" % str(resp.status))
                return True
            except Exception as e:
                print("Exception --> " + str(e.status) + " " + str(e.reason))
                print('Failed to delete Pod: ' + str(e))
                return False

    @staticmethod
    def delete_pods(namesOfpods, namespace):
        k8s = client.CoreV1Api()
        k8s.list_node()
        try:
            for podName in namesOfpods:
                resp = k8s.delete_namespaced_pod(name=podName, namespace=namespace)
                print("Pod with name " + podName + " deleted. status='%s'" % str(resp.status))
            return True
        except Exception as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))
            print('Failed to delete Pod: ' + str(e))
            return False

    @staticmethod
    def delete_pod(name, namespace):
        k8s = client.CoreV1Api()
        k8s.list_node()
        try:
            resp = k8s.delete_namespaced_pod(name=name, namespace=namespace)
            print("Pod with name " + name + " deleted. status='%s'" % str(resp.status))
            return True
        except Exception as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))
            print('Failed to delete Pod: ' + str(e))
            return False

    @staticmethod
    def delete_deployment(fileYaml, namespace):
        with open(path.join(path.dirname(__file__), fileYaml)) as f:
            dep = yaml.safe_load(f)

            k8s = client.ExtensionsV1beta1Api()
            try:
                resp = k8s.delete_namespaced_deployment(name=str(dep['metadata']['name']), namespace=namespace,
                                                        body=client.V1DeleteOptions(propagation_policy="Foreground",
                                                                                    grace_period_seconds=5))
                print("Deployment delete. status='%s'" % str(resp.status))
            except Exception as e:
                print("Exception --> " + str(e.status) + " " + str(e.reason))
                print('Failed to delete Deployment: ' + str(e))

    @staticmethod
    def list_pods():
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs:")
        ret = v1.list_pod_for_all_namespaces(watch=False)
        if len(ret.items) is 0:
            print("No pods are present")
        else:
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    @staticmethod
    def list_pods_for_namespace(namespace):
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs:")
        ret = v1.list_namespaced_pod(watch=False, namespace=namespace)
        if len(ret.items) is 0:
            print("No pods are present")
        else:
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    @staticmethod
    def get_list_pods_for_namespace(namespace):
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs:")
        ret = v1.list_namespaced_pod(watch=False, namespace=namespace)
        if len(ret.items) is 0:
            print("No pods are present")
            return None
        else:
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
            return ret.items

    @staticmethod
    def get_list_podsName_for_namespace(namespace):
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs:")
        ret = v1.list_namespaced_pod(watch=False, namespace=namespace)
        if len(ret.items) is 0:
            print("No pods are present")
            return None
        else:
            names=[]
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
                names.append(i.metadata.name)
            return names

    @staticmethod
    def get_pod_info(name):
        v1 = client.CoreV1Api()
        print("pod request: " + name)
        ret = v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            if (i.metadata.name == name):
                return i

    @staticmethod
    def get_resources(self):
        v1 = client.CoreV1Api()
        try:
            api_response = v1.get_api_resources()
            print(api_response)
        except Exception as e:
            print("Exception when calling CoreV1Api->get_api_resources: %s\n" % e)

    @staticmethod
    def get_status_node(nodename):
        v1 = client.CoreV1Api()
        try:
            status = v1.read_node_status(name=nodename)
            # print(api_response)
            return status
        except Exception as e:
            print("Exception when calling CoreV1Api->read_node_status: %s\n" % e)

    @staticmethod
    def get_node(nodename):
        v1 = client.CoreV1Api()
        try:
            node_info = v1.read_node(name=nodename, pretty=True, exact=True)
            return node_info
        except Exception as e:
            print("Exception when calling CoreV1Api->read_node: %s\n" % e)

    @staticmethod
    def get_nodes():
        v1 = client.CoreV1Api()
        try:
            nodes = v1.list_node()
            if len(nodes.items) is 0:
                print("No pods are present")
            else:
                return nodes
        except Exception as e:
            print("Exception when calling CoreV1Api->read_node: %s\n" % e)

    @staticmethod
    def get_namespace(nodename):
        v1 = client.CoreV1Api()
        try:
            namespace_info = v1.read_namespace(name=nodename)
            # print(api_response)
            return namespace_info
        except Exception as e:
            print("Exception when calling CoreV1Api->read_namespace: %s\n" % e)

    @staticmethod
    def exec_on_pod(podName, namespace, command):
        try:
            v1 = client.CoreV1Api()
            # v1.connect_get_namespaced_pod_exec(podName,namespace,command=command,stderr=True, stdin=True, stdout=True, tty=False, preload_content=False)
            # resp = stream.stream(v1.connect_get_namespaced_pod_exec,podName,namespace,command=command,stderr=True, stdin=True, stdout=True,tty=True)
            # print("Response: " + resp)

            # calling exec and wait for response.
            exec_command = [
                '/bin/sh',
                '-c',
                'echo This message goes to stderr >&2; echo This message goes to stdout']
            resp1 = stream.stream(v1.connect_get_namespaced_pod_exec, podName, namespace,
                                  command=command,
                                  stderr=True, stdin=False,
                                  stdout=True, tty=False)
            print("Response: " + resp1)

            # Calling exec interactively.
            resp = stream.stream(v1.connect_get_namespaced_pod_exec, podName, namespace,
                                 command=command,
                                 stderr=True, stdin=True,
                                 stdout=True, tty=False,
                                 _preload_content=False)
            commands = [
                "vlc",
                "echo \"This message goes to stderr\" >&2",
            ]
            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    print("STDOUT: %s" % resp.read_stdout())
                if resp.peek_stderr():
                    print("STDERR: %s" % resp.read_stderr())
                if commands:
                    c = commands.pop(0)
                    print("Running command... %s\n" % c)
                    resp.write_stdin(c + "\n")
                else:
                    break

            resp.write_stdin("date\n")
            sdate = resp.readline_stdout(timeout=3)
            print("Server date command returns: %s" % sdate)
            resp.write_stdin("whoami\n")
            user = resp.readline_stdout(timeout=3)
            print("Server user is: %s" % user)
            resp.close()

            print(resp)
        except Exception as e:
            print("Exception --> " + str(e.status) + " " + str(e.reason))
            print('Failed to exec command on Pod: ' + str(e))
