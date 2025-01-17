class Component:

    def __init__(self, name=None, boot_dependencies=None, function=None, nodes_blacklist=None, nodes_whitelist=None, parameters=None):
        self.name = name
        self.function = function    #{}
        self.parameters = parameters  #{}
        self.boot_dependencies = boot_dependencies  #[]
        self.nodes_blacklist = nodes_blacklist  #[]
        self.nodes_whitelist = nodes_whitelist  #[]

    def to_dict(self):
        component = dict()
        component["name"] = self.name
        component["function"] = self.function
        component["parameters"] = self.parameters
        component["boot_dependencies"] = self.boot_dependencies
        component["nodes_blacklist"] = self.nodes_blacklist
        component["nodes_whitelist"] = self.nodes_whitelist
        return component

    def parse_dict(self, adv_message):
        self.name = adv_message["name"]
        self.function = adv_message["function"]
        self.parameters = adv_message["parameters"]
        self.boot_dependencies = adv_message["boot_dependencies"]
        self.nodes_blacklist = adv_message["nodes_blacklist"]
        self.nodes_whitelist = adv_message["nodes_whitelist"]
