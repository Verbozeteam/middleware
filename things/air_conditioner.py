from things.thing import Thing
from logs import Log
import json

class SplitAC(Thing):
    def __init__(self, ac_json):
        super(SplitAC, self).__init__()
        self.listening_ports = ac_json.get("ports", [])
        self.id = "split-ac-" + self.listening_ports[0]

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "split_acs"

    def on_hardware_data(self, port, value):
        pass

    def on_controller_data(self, data):
        pass

    def get_state(self):
        return {}

class CentralAC(Thing):
    def __init__(self, ac_json):
        super(CentralAC, self).__init__()
        self.listening_ports = ac_json.get("ports", [])
        self.id = "central-ac-" + self.listening_ports[0] + "-" + self.listening_ports[1]
        self.current_temperature = 25
        self.temperature_port = self.listening_ports[1]

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "central_acs"

    def on_hardware_data(self, port, value):
        if port == self.temperature_port:
            self.current_temperature = value
            self.dirty = True

    def on_controller_data(self, data):
        pass

    def get_state(self):
        return {}
