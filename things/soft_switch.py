from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from things.light import LightSwitch
from logs import Log
import json

class SoftSwitch(Thing):
    def __init__(self, blueprint, J):
        super(SoftSwitch, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("light_id", is_required=True), # ID of the light that this switch switches

            InputPortSpec("switch_port", 0, is_required=True), # Port of the soft switch

            GlobalSubParamSpec("pressed_state", 1), # Default on-state for all ports: on-state is the state when the port is considered PRESSED (1 means HIGH when active, 0 means LOW when active)
            GlobalSubParamSpec("use_pullup", lambda params: params.get("pressed_state") == 0), # whether or not to use pull up resistor of all pin by default
        ])
        self.id = J.get("id", "softswitch-" + self.params.get("switch_port"))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.debounce_timeout = -1
        self.last_read_value = 1 - self.params.get("switch_port", "pressed_state")
        self.button_state = 1 - self.params.get("switch_port", "pressed_state")

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "soft_switches"

    def set_hardware_state(self, port, value):
        super(SoftSwitch, self).set_hardware_state(port, value)
        if port == self.params.get("switch_port") and value != self.last_read_value:
            self.last_read_value = value
            self.debounce_timeout = self.blueprint.core.cur_time_s + 0.05 # 50ms
        return False

    def on_state_changed(self, old_state, new_state):
        if new_state == self.params.get("switch_port", "pressed_state"):
            thing = self.blueprint.get_thing(self.params.get("light_id"))
            if thing:
                new_intensity = 0 if thing.intensity != 0 else (1 if thing.get_blueprint_tag() == LightSwitch.get_blueprint_tag() else 100)
                thing.set_state({"intensity": new_intensity})

    def update(self, cur_time_s):
        if self.debounce_timeout > 0 and cur_time_s > self.debounce_timeout:
            self.debounce_timeout = -1
            if self.last_read_value != self.button_state:
                prev_state = self.button_state
                self.button_state = self.last_read_value
                self.on_state_changed(prev_state, self.button_state)
        elif self.debounce_timeout > 0:
            return True

        return False

class TwoWaySwitch(SoftSwitch):
    def __init__(self, blueprint, switch_json):
        self.id = switch_json.get("id", "twowayswitch-" + switch_json["switch_port"])
        super(TwoWaySwitch, self).__init__(blueprint, switch_json)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "two_way_switches"

    def on_state_changed(self, old_state, new_state):
        thing = self.blueprint.get_thing(self.params.get("light_id"))
        if thing:
            new_intensity = 0 if thing.intensity != 0 else (1 if thing.get_blueprint_tag() == LightSwitch.get_blueprint_tag() else 100)
            thing.set_state({"intensity": new_intensity})

class DNDSoftSwitch(SoftSwitch):
    def __init__(self, blueprint, switch_json):
        self.id = switch_json.get("id", "dndsoftswitch-" + switch_json["switch_port"])
        super(DNDSoftSwitch, self).__init__(blueprint, switch_json)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dnd_soft_switches"

    def on_state_changed(self, old_state, new_state):
        if new_state == self.params.get("switch_port", "pressed_state"):
            thing = list(filter(lambda t: t.get_blueprint_tag() == "hotel_controls", self.blueprint.get_things()))
            if len(thing) > 0:
                thing = thing[0]
                thing.set_state({"do_not_disturb": 1 - thing.do_not_disturb, "room_service": 0})

class RSSoftSwitch(SoftSwitch):
    def __init__(self, blueprint, switch_json):
        self.id = switch_json.get("id", "rssoftswitch-" + switch_json["switch_port"])
        super(RSSoftSwitch, self).__init__(blueprint, switch_json)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "rs_soft_switches"

    def on_state_changed(self, old_state, new_state):
        if new_state == self.params.get("switch_port", "pressed_state"):
            thing = list(filter(lambda t: t.get_blueprint_tag() == "hotel_controls", self.blueprint.get_things()))
            if len(thing) > 0:
                thing = thing[0]
                thing.set_state({"room_service": 1 - thing.room_service, "do_not_disturb": 0})
