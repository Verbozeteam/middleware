from things.thing import Thing
from logs import Log
import json

class HoneywellThermostatT7560(Thing):
    def __init__(self, blueprint, thermostat_json):
        super(HoneywellThermostatT7560, self).__init__(blueprint, thermostat_json)
        self.port_array = ["d41", "d45", "d49", "d51", "d47", "d43", "a14", "a15"]
        for p in self.port_array:
            self.output_ports[p] = 1
        self.id = thermostat_json.get("id", "honeywell-thermostat")
        self.current_temperature = 25
        self.fan_speeds = ["Off", "Low", "Medium", "High", "Auto"]
        self.set_set_point(25)
        self.set_fan_speed(1)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "honeywell_thermostat_t7560"

    def set_fan_speed(self, speed):
        self.current_fan_speed = int(min(max(speed, 0), len(self.fan_speeds)-1))

    def set_set_point(self, set_pt):
        self.current_set_point = float(min(max(set_pt, 12.0), 30.0))

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
            state[self.port_array[i]] = (iset_point >> i) & 0x1
        for i in range(0, 3):
            state[self.port_array[5+i]] = (self.current_fan_speed >> i) & 0x1
        return state

    def set_hardware_state(self, port, value):
        super(HoneywellThermostatT7560, self).set_hardware_state(port, value)
        if port == self.temperature_port:
            self.current_temperature = float(value) / 4.0
        return False

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
        }

