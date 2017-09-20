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
        if data["curtain"] == 0:
            self.pending_commands += [(self.listening_ports[0], 0), (self.listening_ports[1], 0)]
        elif data["curtain"] == 1:
            self.pending_commands.append((self.listening_ports[0], 1))
        elif data["curtain"] == 2:
            self.pending_commands.append((self.listening_ports[1], 1))

    def get_state(self):
        return {}
