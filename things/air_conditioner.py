from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class SplitAC(Thing):
    def __init__(self, blueprint, ac_json):
        super(SplitAC, self).__init__(blueprint, ac_json)
        self.id = ac_json.get("id", "split-ac-unimplemented")

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "split_acs"

class CentralAC(Thing):
    def __init__(self, blueprint, J):
        super(CentralAC, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("min_temperature", 12), # Minimum temperature
            ParamSpec("max_temperature", 30), # Maximum temperature
            ParamSpec("default_sleep_temperature", 25), # Default temperasture when asleep
            ParamSpec("default_wakeup_temperature", 25), # Default temperature when awoken
            ParamSpec("has_auto", False), # whether or not there is auto fan speed

            InputPortSpec("temperature_port", 5000, is_required=True), # Temperature reading port
            InputPortSpec("smoke_detector_port", 0), # Smoke detector reading port (when on, AC fan turns off)

            OutputPortSpec("fan_low_port"), # Fan LOW port
            OutputPortSpec("fan_med_port"), # Fan MEDIUM port
            OutputPortSpec("fan_high_port"), # Fan HIGH port
            OutputPortSpec("valve_port", True), # Modulating valve output port (PWM output)
            OutputPortSpec("digital_valve_port"), # Digital valve output port

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
            GlobalSubParamSpec("use_pullup", lambda params: params.get("on_state") == 0), # whether or not to use pull up resistor of all pin by default
        ])
        self.id = J.get("id", "central-ac-" + self.params.get("temperature_port"))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.fan_speeds = []
        if self.params.get("fan_low_port"):
            self.fan_speeds.append("Low")
        if self.params.get("fan_med_port"):
            self.fan_speeds.append("Med")
        if self.params.get("fan_high_port"):
            self.fan_speeds.append("High")
        if self.params.get("has_auto"):
            self.fan_speeds.append("Auto")

        self.current_set_point = int((self.params.get("max_temperature")+self.params.get("min_temperature"))/2)
        self.current_temperature = self.current_set_point
        self.current_fan_speed = 1
        self.homeostasis = 0.24 # can be actually double that in the worst case (because of temperature rounding)
        self.current_airflow = 0
        self.next_valve_update = 0
        self.is_temp_rising = False
        self.digital_valve_output = 0
        self.smoke_detector_value = 1 - self.params.get("smoke_detector_port", "on_state")

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "central_acs"

    def set_fan_speed(self, speed):
        self.current_fan_speed = int(min(max(speed, 0), len(self.fan_speeds)))

    def set_set_point(self, set_pt):
        self.current_set_point = float(min(max(set_pt, self.params.get("min_temperature")), self.params.get("max_temperature")))

    def sleep(self, source=None):
        super(CentralAC, self).sleep(source)
        if not hasattr(self, "saved_wakeup_temperature"):
            self.saved_wakeup_temperature = self.current_set_point
            self.saved_wakeup_fan = self.current_fan_speed

        if self.params.get("default_sleep_temperature") != None:
            self.set_set_point(self.params.get("default_sleep_temperature"))
            self.set_fan_speed(1) # fan must be on
        else:
            self.set_set_point(25.0)
            self.set_fan_speed(1) # fan must be on

    def wake_up(self, source=None):
        super(CentralAC, self).wake_up(source)
        if self.params.get("default_wakeup_temperature") != None:
            self.set_set_point(self.params.get("default_wakeup_temperature"))
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
        if port == self.params.get("temperature_port"):
            self.current_temperature = float(value) / 4.0
        elif port == self.params.get("smoke_detector_port"):
            self.smoke_detector_value = int(value)
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
        if self.params.get("smoke_detector_port") and self.smoke_detector_value == self.params.get("smoke_detector_port", "on_state"):
            self.current_fan_speed = 0

        if cur_time_s >= self.next_valve_update:
            self.next_valve_update = cur_time_s + 5

            target_temperature = self.current_set_point if self.current_fan_speed > 0 else 50.0

            if self.params.get("valve_port"):
                temp_diff = self.current_temperature - target_temperature
                coeff = (min(max(temp_diff, -10), 10)) / 10; # [-1, 1]
                self.current_airflow = min(max(self.current_airflow + self.homeostasis * coeff, 0.0), 255.0)
            if self.params.get("digital_valve_port"):
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
        return False

    def get_state(self):
        return {
            "temp": self.current_temperature,
            "set_pt": self.current_set_point,
            "fan": self.current_fan_speed,
        }

    def get_hardware_state(self):
        state = {}
        i = 1
        for speed in self.fan_speeds:
            f_on_state = self.params.get("fan_"+speed.lower()+"_port", "on_state")
            if f_on_state != None: # this is low/med/high speed, check if selected then set output port in state to 1 (0 otherwise)
                state[self.params.get("fan_"+speed.lower()+"_port")] = f_on_state if i == self.current_fan_speed else 1 - f_on_state
            elif i == self.current_fan_speed: # this is auto speed and it is selected
                highest_fan_speed = filter(lambda fs: self.params.get("fan_"+fs.lower()+"_port") != None, self.fan_speeds)[-1]
                f_on_state = self.params.get("fan_"+highest_fan_speed.lower()+"_port", "on_state")
                state[self.params.get("fan_"+highest_fan_speed.lower()+"_port")] = f_on_state if int(self.digital_valve_output) else 1 - f_on_state
            i += 1
        if self.params.get("valve_port"):
            state[self.params.get("valve_port")] = int(self.current_airflow)
        if self.params.get("digital_valve_port"):
            state[self.params.get("digital_valve_port")] = int(self.digital_valve_output) if self.params.get("digital_valve_port", "on_state") == 1 else 1 - int(self.digital_valve_output)
        return state

    def get_metadata(self):
        return {
            "fan_speeds": self.fan_speeds,
            "temp_range": [self.params.get("min_temperature"), self.params.get("max_temperature")],
        }
