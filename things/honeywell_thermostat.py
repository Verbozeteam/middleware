from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class HoneywellThermostatT7560(Thing):
    def __init__(self, blueprint, J):
        super(HoneywellThermostatT7560, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("min_temperature", 19), # Minimum temperature
            ParamSpec("max_temperature", 27), # Maximum temperature
            ParamSpec("port_array", ["d41", "d45", "d49", "d51", "d47", "d43", "a14", "a15"]), # Port array for the pins of the TLC

            InputPortSpec("temperature_port", 5000, is_required=True), # Temperature reading port
        ])
        self.id = J.get("id", "honeywell-thermostat")

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        for p in self.params.get("port_array"):
            self.output_ports[p] = 1

        self.current_temperature = int((self.params.get("max_temperature")+self.params.get("min_temperature"))/2)
        self.fan_speeds = ["Low", "Med", "High", "Auto"]
        self.set_set_point(self.current_temperature)
        self.set_fan_speed(1)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "honeywell_thermostat_t7560"

    def set_fan_speed(self, speed):
        self.current_fan_speed = int(min(max(speed, 0), len(self.fan_speeds)))

    def set_set_point(self, set_pt):
        self.current_set_point = float(min(max(set_pt, 12.0), 30.0))

    def set_hardware_state(self, port, value):
        super(HoneywellThermostatT7560, self).set_hardware_state(port, value)
        if port == self.params.get("temperature_port"):
            self.current_temperature = float(value) / 4.0
        return False

    def get_state(self):
        return {
            "temp": self.current_temperature,
            "set_pt": self.current_set_point,
            "fan": self.current_fan_speed,
        }

    def get_hardware_state(self):
        state = {}
        iset_point = int(self.current_set_point) - 12
        # 5 bits for set pt, 3 for fan speed
        for i in range(0, 5):
            state[self.params.get("port_array")[i]] = (iset_point >> i) & 0x1
        for i in range(0, 3):
            state[self.params.get("port_array")[5+i]] = (self.current_fan_speed >> i) & 0x1
        return state

    def set_state(self, data, token_from="system"):
        super(HoneywellThermostatT7560, self).set_state(data, token_from)
        if "set_pt" in data:
            self.set_set_point(data["set_pt"])
        if "fan" in data:
            self.set_fan_speed(data["fan"])
        return False

    def get_metadata(self):
        return {
            "fan_speeds": self.fan_speeds,
            "temp_range": [self.params.get("min_temperature"), self.params.get("max_temperature")],
        }

