from things.thing import Thing
from logs import Log
import json

class Curtain(Thing):
    def __init__(self, blueprint, curtain_json):
        super(Curtain, self).__init__(blueprint, curtain_json)
        self.output_ports[self.up_port] = 1 # digital output
        self.output_ports[self.down_port] = 1 # digital output
        self.id = "curtain-" + self.up_port + "-" + self.down_port

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "curtains"

    def on_controller_data(self, data):
        if data["curtain"] == 0: # stop curtain
            self.pending_commands += [(self.up_port, 0), (self.down_port, 0)]
        elif data["curtain"] == 1: # curtain up
            self.pending_commands += [(self.up_port, 1), (self.down_port, 0)]
        elif data["curtain"] == 2: # curtain down
            self.pending_commands += [(self.down_port, 1), (self.up_port, 0)]

    def get_state(self):
        return {}
