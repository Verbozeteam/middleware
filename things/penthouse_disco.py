from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class PenthouseDisco(Thing):
    def __init__(self, blueprint, J):
        super(PenthouseDisco, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            InputPortSpec("open_contactor_1", 0, is_required=True), # First open contactor input
            InputPortSpec("close_contactor_1", 0, is_required=True), # First close contactor input
            InputPortSpec("open_contactor_2", 0, is_required=True), # Second open contactor input
            InputPortSpec("close_contactor_2", 0, is_required=True), # Second close contactor input

            OutputPortSpec("fog_output", is_required=True), # Fog outport port
            OutputPortSpec("exhaust_output", is_required=True), # Exhaust outport port
            OutputPortSpec("lights_output", is_required=True), # Lights outport port
            OutputPortSpec("open_motor", is_required=True), # Open motor outport port
            OutputPortSpec("close_motor", is_required=True), # Close motor outport port

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
            GlobalSubParamSpec("use_pullup", False), # whether or not to use pull up resistor of all pin by default
        ])
        self.id = J.get("id", "penthouse-disco")

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

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
        if port == self.params.get("open_contactor_1"):
            self.open_contactors[0] = value == self.params.get("open_contactor_1", "on_state")
        if port == self.params.get("open_contactor_2"):
            self.open_contactors[1] = value == self.params.get("open_contactor_2", "on_state")
        if port == self.params.get("close_contactor_1"):
            self.close_contactors[0] = value == self.params.get("close_contactor_1", "on_state")
        if port == self.params.get("close_contactor_2"):
            self.close_contactors[1] = self.params.get("close_contactor_2", "on_state")
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
            self.params.get("open_motor"): self.params.get("open_motor", "on_state") if self.is_opening else 1 - self.params.get("open_motor", "on_state"),
            self.params.get("close_motor"): self.params.get("close_motor", "on_state") if self.is_closing else 1 - self.params.get("close_motor", "on_state"),
        }
        if self.params.get("fog_output"): state[self.params.get("fog_output")] = self.params.get("fog_output", "on_state") if self.is_fogging else 1 - self.params.get("fog_output", "on_state")
        if self.params.get("exhaust_output"): state[self.params.get("exhaust_output")] = self.params.get("exhaust_output", "on_state") if self.is_exhausting else 1 - self.params.get("exhaust_output", "on_state")
        if self.params.get("lights_output"): state[self.params.get("lights_output")] = self.params.get("lights_output", "on_state") if self.is_lighting else 1 - self.params.get("lights_output", "on_state")
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
            "has_fog": self.params.get("fog_output"),
            "has_exhaust": self.params.get("exhaust_output"),
            "has_lights": self.params.get("lights_output"),
        }


