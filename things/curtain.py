from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class Curtain(Thing):
    def __init__(self, blueprint, J):
        super(Curtain, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("max_move_time", 10000), # Maximum time required to fully open/close a curtain

            OutputPortSpec("up_port", is_required=True), # Curtain DOWN output port
            OutputPortSpec("down_port", is_required=True), # Curtain UP output port

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
        ])
        self.id = J.get("id", "curtain-" + self.params.get("up_port") + "-" + self.params.get("down_port"))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

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
        return {
            "curtain": 0 if (self.up_output == self.down_output) else (1 if self.up_output == 1 else 2)
        }

    def get_hardware_state(self):
        return {
            self.params.get("up_port"): self.up_output if self.params.get("up_port", "on_state") == 1 else 1 - self.up_output,
            self.params.get("down_port"): self.down_output if self.params.get("down_port", "on_state") == 1 else 1 - self.down_output,
        }

    def get_metadata(self):
        return {
            "max_move_time": self.params.get("max_move_time")
        }

