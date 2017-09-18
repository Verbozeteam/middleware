from things.thing import Thing
from logs import Log
import json

class Curtain(Thing):
    def __init__(self, curtain_json):
        super(Curtain, self).__init__()
        self.listening_ports = curtain_json.get("ports", [])
        self.id = "curtain-" + self.listening_ports[0] + "-" + self.listening_ports[1]

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "curtains"

    def on_hardware_data(self, port, value):
        pass

    def on_controller_data(self, data):
        pass

    def get_state(self):
        return {}
