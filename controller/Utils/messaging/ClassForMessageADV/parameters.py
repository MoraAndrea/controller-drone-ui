class Parameter:

    def __init__(self, path=None):

        self.path = path

    def to_dict(self):
        function = dict()
        function["path"] = self.path
        return function

    def parse_dict(self, adv_message):
        self.path = adv_message["path"]
