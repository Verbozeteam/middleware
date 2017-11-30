from things.thing import Thing
from logs import Log
import json

class SplitAC(Thing):
    def __init__(self, blueprint, ac_json):
        super(SplitAC, self).__init__(blueprint, ac_json)
        self.id = ac_json.get("id", "split-ac-" + self.pwm_port)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "split_acs"

class CentralAC(Thing):
    def __init__(self, blueprint, ac_json):
        super(CentralAC, self).__init__(blueprint, ac_json)
        self.input_ports[self.temperature_port] = 5000 # read temperature every 5 seconds
        self.output_ports[self.fan_port] = 1 # digital output
        if hasattr(self, "valve_port"):
            self.output_ports[self.valve_port] = 2 # pwm output
        if hasattr(self, "digital_valve_port"):
            self.output_ports[self.digital_valve_port] = 1 # digital OPEN/CLOSE valve
        self.id = ac_json.get("id", "central-ac-" + self.temperature_port + "-" + self.fan_port)
        self.current_set_point = 25
        self.current_temperature = 25
        self.current_fan_speed = 1
        self.homeostasis = 0.24 # can be actually double that in the worst case (because of temperature rounding)
        self.current_airflow = 0
        self.next_valve_update = 0
        self.is_temp_rising = False
        self.digital_valve_output = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "central_acs"

    def set_fan_speed(self, speed):
        self.current_fan_speed = int(min(max(speed, 0), 2))

    def set_set_point(self, set_pt):
        self.current_set_point = float(min(max(set_pt, 0.0), 50.0))

    def sleep(self):
        super(CentralAC, self).sleep()
        if not hasattr(self, "saved_wakeup_temperature"):
            self.saved_wakeup_temperature = self.current_set_point
            self.saved_wakeup_fan = self.current_fan_speed

        if hasattr(self, "default_sleep_temperature"):
            self.set_set_point(self.default_sleep_temperature)
            self.set_fan_speed(1) # fan must be on
        else:
            self.set_set_point(25.0)
            self.set_fan_speed(1) # fan must be on

    def wake_up(self):
        super(CentralAC, self).wake_up()
        if hasattr(self, "default_wakeup_temperature"):
            self.set_set_point(self.default_wakeup_temperature)
            self.set_fan_speed(1) # fan must be on
        elif hasattr(self, "saved_wakeup_temperature"):
            self.set_set_point(self.saved_wakeup_temperature)
            self.set_fan_speed(self.saved_wakeup_fan)

        if hasattr(self, "saved_wakeup_temperature"):
            delattr(self, "saved_wakeup_temperature")
        if hasattr(self, "saved_wakeup_fan"):
            delattr(self, "saved_wakeup_fan")

    def set_hardware_state(self, port, value):
        super(CentralAC, self).set_hardware_state(port, value)
        if port == self.temperature_port:
            self.current_temperature = float(value) / 4.0
        return False

    def set_state(self, data, token_from="system"):
        super(CentralAC, self).set_state(data, token_from)
        if hasattr(self, "saved_wakeup_temperature"):
            return # block updates while sleeping

        if "set_pt" in data:
            self.set_set_point(data["set_pt"])
        if "fan" in data:
            self.set_fan_speed(data["fan"])
        return False

    def update(self, cur_time_s):
        if cur_time_s >= self.next_valve_update:
            self.next_valve_update = cur_time_s + 5

            target_temperature = self.current_set_point if self.current_fan_speed > 0 else 50.0

            if hasattr(self, "valve_port"):
                temp_diff = self.current_temperature - target_temperature
                coeff = (min(max(temp_diff, -10), 10)) / 10; # [-1, 1]
                self.current_airflow = min(max(self.current_airflow + self.homeostasis * coeff, 0.0), 255.0)
            if hasattr(self, "digital_valve_port"):
                if self.is_temp_rising:
                    if self.current_temperature > target_temperature + self.homeostasis:
                        self.digital_valve_output = 1
                        self.is_temp_rising = False
                    else:
                        self.digital_valve_output = 0
                if not self.is_temp_rising:
                    if self.current_temperature < target_temperature - self.homeostasis:
                        self.digital_valve_output = 0
                        self.is_temp_rising = True
                    else:
                        self.digital_valve_output = 1

    def get_state(self):
        return {
            "temp": self.current_temperature,
            "set_pt": self.current_set_point,
            "fan": self.current_fan_speed,
        }

    def get_hardware_state(self):
        state = {self.fan_port: min(max(int(self.current_fan_speed-1), 0), 1)}
        if hasattr(self, "valve_port"):
            state[self.valve_port] = int(self.current_airflow)
        if hasattr(self, "digital_valve_port"):
            state[self.digital_valve_port] = int(self.digital_valve_output)
        return state
