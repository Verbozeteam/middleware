from things.thing import Thing
from logs import Log
import json

class PenthouseDisco(Thing):
    def __init__(self, blueprint, pd_json):
        super(PenthouseDisco, self).__init__(blueprint, pd_json)
        self.id = pd_json.get("id", "penthouse-disco")
        if not hasattr(self, "input_on_state"):
            self.input_on_state = 1
        if not hasattr(self, "output_on_state"):
            self.output_on_state = 1
        is_using_pullup = self.input_on_state == 0
        if hasattr(self, "use_pullup"):
            is_using_pullup = self.use_pullup
        self.input_ports[self.open_contactor_1] = {"is_pullup": is_using_pullup, "read_interval": 0}
        self.input_ports[self.close_contactor_1] = {"is_pullup": is_using_pullup, "read_interval": 0}
        self.input_ports[self.open_contactor_2] = {"is_pullup": is_using_pullup, "read_interval": 0}
        self.input_ports[self.close_contactor_2] = {"is_pullup": is_using_pullup, "read_interval": 0}
        self.output_ports[self.open_motor] = 1
        self.output_ports[self.close_motor] = 1

        if hasattr(self, "fog_output"):
            self.output_ports[self.fog_output] = 1
        if hasattr(self, "exhaust_output"):
            self.output_ports[self.exhaust_output] = 1
        if hasattr(self, "lights_output"):
            self.output_ports[self.lights_output] = 1

        self.open_contactors = [False, False]
        self.close_contactors = [False, False]
        self.is_opening = False
        self.is_closing = False
        self.is_fogging = False
        self.is_exhausting = False
        self.is_lighting = False

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "penthouse_disco"

    def set_hardware_state(self, port, value):
        super(PenthouseDisco, self).set_hardware_state(port, value)
        if port == self.open_contactor_1:
            self.open_contactors[0] = value == self.input_on_state
        if port == self.open_contactor_2:
            self.open_contactors[1] = value == self.input_on_state
        if port == self.close_contactor_1:
            self.close_contactors[0] = value == self.input_on_state
        if port == self.close_contactor_2:
            self.close_contactors[1] = value == self.input_on_state
        return False

    def get_state(self):
        return {
            "lights": 1 if self.is_lighting else 0,
            "exhaust": 1 if self.is_exhausting else 0,
            "fog": 1 if self.is_fogging else 0,
            "motor": 0 if (not self.is_opening and not self.is_closing) else (1 if self.is_opening else 2),
        }

    def get_hardware_state(self):
        state = {
            self.open_motor: self.output_on_state if self.is_opening else 1 - self.output_on_state,
            self.close_motor: self.output_on_state if self.is_closing else 1 - self.output_on_state,
        }
        if hasattr(self, "fog_output"): state[self.fog_output] = self.output_on_state if self.is_fogging else 1 - self.output_on_state
        if hasattr(self, "exhaust_output"): state[self.exhaust_output] = self.output_on_state if self.is_exhausting else 1 - self.output_on_state
        if hasattr(self, "lights_output"): state[self.lights_output] = self.output_on_state if self.is_lighting else 1 - self.output_on_state
        return state

    def set_state(self, data, token_from="system"):
        super(PenthouseDisco, self).set_state(data, token_from)
        if "motor" in data:
            if data["motor"] == 0:
                self.is_opening = False
                self.is_closing = False
            elif data["motor"] == 1:
                self.is_opening = True
                self.is_closing = False
            elif data["motor"] == 2:
                self.is_opening = False
                self.is_closing = True
        if "fog" in data:
            self.is_fogging = bool(data["fog"])
        if "exhaust" in data:
            self.is_exhausting = bool(data["exhaust"])
        if "lights" in data:
            self.is_lighting = bool(data["lights"])
        return False

    def update(self, cur_time_s):
        if self.is_opening and self.open_contactors == [True, True]:
            self.set_state({"motor": 0, "lights": 1}) # stop motors and turn on light
        if self.is_closing and self.close_contactors == [True, True]:
            self.set_state({"motor": 0, "lights": 0}) # stop motors and turn off light
        return False

    def get_metadata(self):
        return {
            "has_fog": hasattr(self, "fog_output"),
            "has_exhaust": hasattr(self, "exhaust_output"),
            "has_lights": hasattr(self, "lights_output"),
        }


