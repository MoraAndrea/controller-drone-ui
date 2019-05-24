class Component:

    def __init__(self, name=None, app_name=None, function=None):
        self.name = name
        self.app_name = app_name
        self.function = function    #{}

    def to_dict(self):
        component = dict()
        component["name"] = self.name
        component["app_name"] = self.app_name
        component["function"] = self.function
        return component

    def parse_dict(self, adv_message):
        self.name = adv_message["name"]
        self.app_name = adv_message["app_name"]
        self.function = adv_message["function"]

class Function:

    def __init__(self, image=None, resources=None):

        self.image = image
        self.resources = resources  #{}

    def to_dict(self):
        function = dict()
        function["image"] = self.image
        function["resources"] = self.resources
        return function

    def parse_dict(self, adv_message):
        self.image = adv_message["image"]
        self.resources = adv_message["resources"]
