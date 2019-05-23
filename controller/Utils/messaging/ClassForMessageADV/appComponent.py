class Component:

    def __init__(self, name=None, image=None, priority=None, resources=None, blacklist=None, parameter=None):
        self.name = name
        self.image = image
        self.priority = priority
        self.resources = resources
        self.blacklist = blacklist
        self.parameter = parameter

    def to_dict(self):
        component = dict()
        component["name"] = self.name
        component["image"] = self.image
        component["priority"] = self.priority
        component["resources"] = self.resources
        component["blacklist"] = self.blacklist
        component["parameter"] = self.parameter
        return component

    def parse_dict(self, adv_message):
        self.name = adv_message["name"]
        self.image = adv_message["image"]
        self.priority = adv_message["priority"]
        self.resources = adv_message["resources"]
        self.blacklist = adv_message["blacklist"]
        self.parameter = adv_message["parameter"]
