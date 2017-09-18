from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, light_json):
        super(LightSwitch, self).__init__()
        self.listening_ports = light_json.get("ports", [])
        self.id = "lightswitch-" + self.listening_ports[0]

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "light_switches"

    def on_hardware_data(self, port, value):
        pass

    def on_controller_data(self, data):
        pass

    def get_state(self):
        return {}

class Dimmer(Thing):
    def __init__(self, dimmer_json):
        super(Dimmer, self).__init__()
        self.listening_ports = dimmer_json.get("ports", [])
        self.id = "dimmer-" + self.listening_ports[0]

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dimmers"

    def on_hardware_data(self, port, value):
        pass

    def on_controller_data(self, data):
        pass

    def get_state(self):
        return {}
