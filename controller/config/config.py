import configparser
import os
import inspect

from controller.Utils.singleton import Singleton


class Configuration(object, metaclass=Singleton):

    def __init__(self, conf_file='config/config.ini'):

        self.conf_file = conf_file

        config = configparser.RawConfigParser()
        base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))\
            .rpartition('/')[0]
        try:
            if base_folder == "":
                config.read(str(base_folder) + self.conf_file)
            else:
                config.read(str(base_folder) + '/' + self.conf_file)

            # [file]
            self.RESULT = config.get('file', 'result')
            self.REQUEST = config.get('file', 'request')

            # [folder]
            self.YAML_FOLDER=config.get('folder','yaml-folder')

            # [kubernetes]
            self.NAMESPACE=config.get('kubernetes','namespace')

            # [userRabbit]
            self.USERNAME = config.get('userRabbit', 'username')
            self.PASSWORD = config.get('userRabbit', 'password')

            # [federation]
            self.EXCHANGE = config.get('federation','exchange_name')
            self.SET_NAME = config.get('federation', 'set_name')
            self.POLICY_NAME = config.get('federation', 'policy_name')
            self.PATTERN = config.get('federation', 'pattern')
            self.QUEUE_ADV = config.get('federation', 'queue_adv')
            self.QUEUE_RESULT = config.get('federation', 'queue_result')

        except Exception as ex:
            raise Exception(str(ex))
