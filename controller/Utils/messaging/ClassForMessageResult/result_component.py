class Component:

    def __init__(self, name=None, image=None, priority=None, winner=None):
        self.name = name
        self.image = image
        self.priority = priority
        self.winner = winner

    def to_dict(self):
        component = dict()
        component["name"] = self.name
        component["image"] = self.image
        component["priority"] = self.priority
        component["winner"] = self.winner
        return component

    def parse_dict(self, adv_message):
        self.name = adv_message["name"]
        self.image = adv_message["image"]
        self.priority = adv_message["priority"]
        self.winner = adv_message["winner"]
