from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class Telephone(Thing):
    def __init__(self, blueprint, J):
        super(Telephone, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
        ])
        self.id = J.get("id", "telephone")

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "telephone"

    def set_state(self, data, token_from="system"):
        super(Telephone, self).set_state(data, token_from)
        return False

    def get_state(self):
        return {
        }

    def get_hardware_state(self):
        return {
        }

    def get_metadata(self):
        return {
        }

