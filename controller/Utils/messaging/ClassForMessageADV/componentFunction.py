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
