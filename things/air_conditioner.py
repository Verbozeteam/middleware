from things.thing import Thing
from logs import Log
import json

class SplitAC(Thing):
    def __init__(self, ac_json):
        super(SplitAC, self).__init__(ac_json)
        self.id = "split-ac-" + self.pwm_port

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
        super(CentralAC, self).__init__(ac_json)
        self.input_ports[self.temperature_port] = 2000 # read temperature every 2 seconds
        self.output_ports[self.fan_port] = 1 # digital output
        self.output_ports[self.valve_port] = 2 # pwm output
        self.id = "central-ac-" + self.temperature_port + "-" + self.fan_port
        self.current_set_point = 25
        self.current_temperature = 25
        self.current_fan_speed = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "central_acs"

    def on_hardware_data(self, port, value):
        if port == self.temperature_port:
            self.current_temperature = float(value) / 2.0
            self.dirty = True
        elif port == self.fan_port:
            self.current_fan_speed = value
            self.dirty = True

    def on_controller_data(self, data):
        if "set_pt" in data:
            self.current_set_point = float(data["set_pt"])
        elif "fan" in data:
            self.current_fan_speed = data["fan"]
            self.dirty = True
            self.pending_commands.append((self.digital_writing_ports[0], self.current_fan_speed))

    def update(self, cur_time_s):
        print ("hola")

    def get_state(self):
        return {
            "temp": self.current_temperature,
            "set_pt": self.current_set_point,
        }
