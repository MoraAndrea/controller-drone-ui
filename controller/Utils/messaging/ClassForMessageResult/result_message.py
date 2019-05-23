from controller.Utils import parse_json

class resultMessage:

    def __init__(self, ID=None, components=None):
        self.ID = ID
        self.components = components
        pass

    def to_dict(self):
        result_message = dict()
        result_message["ID"] = self.ID
        result_message["components"] = self.components
        return result_message

    def parse_dict(self, result_message):
        self.ID=result_message["ID"]
        self.components = result_message["components"]

    def from_json(self, filename):
        file= parse_json.parse_json_file(filename)
        self.ID = file['ID']
        self.components = file['components']
