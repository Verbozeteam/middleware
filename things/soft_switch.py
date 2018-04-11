from things.thing import Thing
from things.light import LightSwitch
from logs import Log
import json

class SoftSwitch(Thing):
    def __init__(self, blueprint, light_json):
        super(SoftSwitch, self).__init__(blueprint, light_json)
        self.id = light_json.get("id", "softswitch-" + self.light_id)
        if not hasattr(self, "pressed_state"):
            self.pressed_state = 1
        self.input_ports[self.switch_port] = {
            "read_interval": 0,
            "is_pullup": self.pressed_state == 0,
        }
        self.debounce_timeout = -1
        self.last_read_value = 1 - self.pressed_state
        self.button_state = 1 - self.pressed_state

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "soft_switches"

    def set_hardware_state(self, port, value):
        super(SoftSwitch, self).set_hardware_state(port, value)
        if port == self.switch_port and value != self.last_read_value:
            self.last_read_value = value
            self.debounce_timeout = self.blueprint.core.cur_time_s + 0.05 # 50ms
        return False

    def on_state_changed(self, old_state, new_state):
        if new_state == self.pressed_state:
            thing = self.blueprint.get_thing(self.light_id)
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
    def __init__(self, blueprint, light_json):
        self.id = light_json.get("id", "twowayswitch-" + light_json["light_id"])
        super(TwoWaySwitch, self).__init__(blueprint, light_json)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "two_way_switches"

    def on_state_changed(self, old_state, new_state):
        thing = self.blueprint.get_thing(self.light_id)
        if thing:
            new_intensity = 0 if thing.intensity != 0 else (1 if thing.get_blueprint_tag() == LightSwitch.get_blueprint_tag() else 100)
            thing.set_state({"intensity": new_intensity})
