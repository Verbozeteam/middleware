from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, blueprint, light_json):
        super(LightSwitch, self).__init__(blueprint, light_json)
        self.output_ports[self.switch_port] = 1 # digital output
        self.id = "lightswitch-" + self.switch_port
        self.intensity = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "light_switches"

    def on_controller_data(self, data):
        if "intensity" in data:
            self.intensity = data["intensity"]
            self.dirty = True
            self.pending_commands.append((self.switch_port, self.intensity))

    def get_state(self):
        return {
            "intensity": self.intensity
        }

class Dimmer(Thing):
    def __init__(self, blueprint, dimmer_json):
        super(Dimmer, self).__init__(blueprint, dimmer_json)
        self.output_ports[self.pwm_port] = 2 # pwm output
        self.id = "dimmer-" + self.pwm_port
        self.intensity = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dimmers"

    def on_controller_data(self, data):
        self.intensity = data["intensity"]
        self.dirty = True
        self.pending_commands.append((self.pwm_port, int(self.intensity * 2.55)))

    def get_state(self):
        return {
            "intensity": self.intensity
        }
