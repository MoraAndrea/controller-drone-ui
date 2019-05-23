import docker

from controller.Utils import singleton


class DockerClass(object, metaclass=singleton.Singleton):
    """
    This class manage Docker communication
    """

    def __init__(self):
        self._client=docker.from_env()

    @staticmethod
    def create_image(self, image_tag):
        try:
            s=self._client.images.build(path="./Docker_vlc_work/",tag=image_tag, rm=True)
            print(s)
        except Exception as e:
            print("Exception --> "+str(e))
        self.print_images()

    @staticmethod
    def remove_image(self,image_tag):
        try:
            s=self._client.images.remove(image=image_tag)
            print(s)
        except Exception as e:
            print("Exception --> " + str(e))
        self.print_images()

    @staticmethod
    def print_images(self):
        print("--> List of local images:")
        images_list=self._client.images.list()
        print(*images_list, sep = '\n')

    @staticmethod
    def get_images(self):
        return self._client.images.list()

    @staticmethod
    def get_image(self, name):
        try:
            image=self._client.images.get(name)
            #print("--> Image found: " + image.tags[0])
            return image
        except Exception as e:
            print("Exception --> "+str(e))
            return False

    @staticmethod
    def run_container(self, image):
        #sudo docker run -ti --rm  -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix vlc
        container=None
        try:
            container=self._client.containers.run(image=image,volumes=["/tmp/.X11-unix:/tmp/.X11-unix"],environment=["DISPLAY=:0.0"],
                                            tty=True,stdin_open=True, stderr=True,stdout=True,remove=True,detach=True)
            print(container)
        except Exception as e:
            print("Exception --> "+str(e))
        return container

    @staticmethod
    def exec_command(container,command):
        container.exec_run(cmd=command,tty=True,detach=True, stdin=True)