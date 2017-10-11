from things.thing import Thing
from logs import Log
import json

class SplitAC(Thing):
    def __init__(self, blueprint, ac_json):
        super(SplitAC, self).__init__(blueprint, ac_json)
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
    def __init__(self, blueprint, ac_json):
        super(CentralAC, self).__init__(blueprint, ac_json)
        self.input_ports[self.temperature_port] = 3000 # read temperature every 3 seconds
        self.output_ports[self.fan_port] = 1 # digital output
        self.output_ports[self.valve_port] = 2 # pwm output
        self.id = "central-ac-" + self.temperature_port + "-" + self.fan_port
        self.current_set_point = 25
        self.current_temperature = 25
        self.current_fan_speed = 1
        self.homeostasis = 0.49
        self.current_airflow = 0
        self.next_airflow_update = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "central_acs"

    def set_fan_speed(self, speed):
        self.current_fan_speed = speed
        self.dirty = True
        self.pending_commands.append((self.fan_port, self.current_fan_speed))

    def set_set_point(self, set_pt):
        self.current_set_point = float(set_pt)
        self.dirty = True

    def sleep(self):
        self.saved_wakeup_temperature = self.current_set_point
        self.saved_wakeup_fan = self.current_fan_speed
        if hasattr(self, "default_sleep_temperature"):
            self.set_set_point(self.default_sleep_temperature)
            self.set_fan_speed(1) # fan must be on
        else:
            self.set_set_point(25.0)
            self.set_fan_speed(0) # turn off the fan

    def wake_up(self):
        if hasattr(self, "default_wakeup_temperature"):
            self.set_set_point(self.default_wakeup_temperature)
            self.set_fan_speed(1) # fan must be on
        elif hasattr(self, "saved_wakeup_temperature"):
            self.set_set_point(self.saved_wakeup_temperature)
            self.set_fan_speed(self.saved_wakeup_fan)

    def on_new_hardware(self):
        self.set_fan_speed(self.current_fan_speed)
        self.set_set_point(self.current_set_point)

    def on_hardware_data(self, port, value):
        if port == self.temperature_port:
            self.current_temperature = float(value) / 2.0
            self.dirty = True

    def on_controller_data(self, data):
        if "set_pt" in data:
            self.set_set_point(data["set_pt"])
        if "fan" in data:
            self.set_fan_speed(data["fan"])

    def update(self, cur_time_s):
        temp_diff = self.current_temperature - self.current_set_point
        coeff = (min(max(temp_diff, -10), 10)) / 10; # [-1, 1]
        self.current_airflow = min(max(self.current_airflow + self.homeostasis * coeff, 0.0), 255.0)
        if cur_time_s >= self.next_airflow_update:
            self.next_airflow_update = cur_time_s + 2
            self.pending_commands.append((self.valve_port, int(self.current_airflow)))

    def get_state(self):
        return {
            "temp": self.current_temperature,
            "set_pt": self.current_set_point,
            "fan": self.current_fan_speed,
        }
