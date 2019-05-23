class Resource:

    def __init__(self, memory=None, cpu=None):
        self.memory = memory
        self.cpu = cpu

    def to_dict(self):
        component = dict()
        component["memory"] = self.memory
        component["cpu"] = self.cpu
        return component

    def parse_dict(self, adv_message):
        self.memory = adv_message["memory"]
        self.cpu = adv_message["cpu"]
