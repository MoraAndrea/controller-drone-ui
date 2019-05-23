from controller.Utils import parse_json

class AdvMessage:

    def __init__(self, ID=None, owner=None, components=None, type=None):
        self.ID = ID
        self.owner = owner
        self.components = components    #[str, component]
        self.type = type

    def to_dict(self):
        adv_message = dict()
        adv_message["ID"]=self.ID
        adv_message["owner"] = self.owner
        adv_message["components"] = self.components
        adv_message["type"] = self.type
        return adv_message

    def parse_dict(self, adv_message):
        self.ID=adv_message["ID"]
        self.owner = adv_message["owner"]
        self.components = adv_message["components"]
        self.type = adv_message["type"]

    def from_json(self, filename):
        file= parse_json.parse_json_file(filename)
        self.ID = file['ID']
        self.owner = file['owner']
        self.components = file['components']
        self.type = file['type']
