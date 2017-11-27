from things.thing import Thing
from logs import Log
import json

class Curtain(Thing):
    def __init__(self, blueprint, curtain_json):
        super(Curtain, self).__init__(blueprint, curtain_json)
        self.output_ports[self.up_port] = 1 # digital output
        self.output_ports[self.down_port] = 1 # digital output
        self.id = "curtain-" + self.up_port + "-" + self.down_port
        self.up_output = 0
        self.down_output = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "curtains"

    def set_state(self, data, token_from="system"):
        super(Curtain, self).set_state(data, token_from)
        if "curtain" in data:
            if data["curtain"] == 0: # stop curtain
                self.up_output = 0
                self.down_output = 0
            elif data["curtain"] == 1: # curtain up
                self.up_output = 1
                self.down_output = 0
            elif data["curtain"] == 2: # curtain down
                self.up_output = 0
                self.down_output = 1
        return False

    def get_state(self):
        return {}

    def get_hardware_state(self):
        return {
            self.up_port: self.up_output,
            self.down_port: self.down_output,
        }
