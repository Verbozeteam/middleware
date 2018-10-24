from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class RoomKey(Thing):
    def __init__(self, blueprint, J):
        super(RoomKey, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("auto_lock_time", 5000), # Time (in ms) before locking the door after it has been unlocked
        ])
        self.id = J.get("id", "room-key") # @TODO: MAKE UNIQUE BASED ON HARDWARE PORT <<<<<<<<<<<<<<<<<<

        self.unlock_time = 0
        self.last_locked_time = 0
        self.is_locked = 1

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "room_keys"

    def set_state(self, data, token_from="system"):
        super(RoomKey, self).set_state(data, token_from)
        if "lock" in data:
            if data["lock"]:
                self.is_locked = 1
            else:
                self.unlock_time = 0
                self.is_locked = 0
        return False

    def update(self, cur_time_s):
        if not self.is_locked and self.unlock_time == 0:
            self.unlock_time = cur_time_s
        if not self.is_locked and cur_time_s - self.unlock_time >= (self.params.get("auto_lock_time") / 1000):
            self.set_state({"lock": 1}) # this will cause the token to be properly set
        return False

    def get_state(self):
        return {
            "lock": self.is_locked,
        }

    def get_hardware_state(self):
        return {
        }

    def get_metadata(self):
        return {
        }

