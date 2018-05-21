from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from things.hotel_controls import HotelControls
from logs import Log
import json

class Bell(Thing):
    def __init__(self, blueprint, J):
        super(Bell, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("ring_timer"), # Timer to keep the output on even after trigger release

            InputPortSpec("bell_input_port", 0), # Optional switch to controls bell_port (and is disabled while in DND)

            OutputPortSpec("bell_port", is_required=True), # Bell activation output port (digital)

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
            GlobalSubParamSpec("use_pullup", lambda params: params.get("on_state") == 0) # whether or not to use pull up resistor of all pin by default
        ])
        self.id = J.get("id", "bell-"+self.params.get('bell_port'))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.is_bell_ringing = 1 if self.params.get("bell_input_port") == None else 0 # always 'ringing' if bell has no switch, otherwise controlled by switch
        self.bell_ring_start = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "bells"

    def set_hardware_state(self, port, value):
        super(Bell, self).set_hardware_state(port, value)
        if port == self.params.get("bell_input_port"):
            if self.params.get("ring_timer") == None: # no timer, control ringing here
                self.is_bell_ringing = 1 if value == self.params.get("bell_input_port", "on_state") else 0
            else: # timer, control ringing in update()
                self.bell_ring_start = self.blueprint.core.cur_time_s
        return False

    def update(self, cur_time_s):
        ring_timer = self.params.get("ring_timer")
        if ring_timer:
            if cur_time_s - self.bell_ring_start < ring_timer:
                self.is_bell_ringing = 1
                return True # need update again to make accurate timer
            else:
                self.is_bell_ringing = 0

        return False

    def get_state(self):
        return {}

    def get_hardware_state(self):
        bell_output = self.is_bell_ringing if self.params.get("bell_port", "on_state") == 1 else 1 - self.is_bell_ringing

        thing = list(filter(lambda t: isinstance(t, HotelControls), self.blueprint.get_things()))
        if len(thing) > 0:
            if thing[0].do_not_disturb:
                bell_output = 1 - self.params.get("bell_port", "on_state")

        return {
            self.params.get("bell_port"): bell_output,
        }
