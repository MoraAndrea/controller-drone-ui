from controller.Utils import parse_json

class AdvMessage:

    def __init__(self, app_name=None, base_node=None, type=None, components=None):
        self.app_name = app_name
        self.base_node = base_node
        self.type = type
        self.components = components    #[]

    def to_dict(self):
        adv_message = dict()
        adv_message["app_name"]=self.app_name
        adv_message["base_node"] = self.base_node
        adv_message["type"] = self.type
        adv_message["components"] = self.components
        return adv_message

    def parse_dict(self, adv_message):
        self.app_name=adv_message["app_name"]
        self.base_node = adv_message["base_node"]
        self.type = adv_message["type"]
        self.components = adv_message["components"]

    def from_json(self, filename):
        file= parse_json.parse_json_file(filename)
        self.app_name = file['app_name']
        self.base_node = file['base_node']
        self.type = file['type']
        self.components = file['components']
