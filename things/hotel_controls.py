from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class HotelControls(Thing):
    def __init__(self, blueprint, J):
        super(HotelControls, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("card_in_state", 1), # voltage reading (0: low, 1: high) when the key card is in the holder
            ParamSpec("nocard_power_timeout", 20), # Timeout to sleep after card is removed in seconds
            ParamSpec("welcome_light_duration", 30), # Duration to keep the welcome light on after door is opened
            ParamSpec("light_sensor_dark_threshold", 255), # Reading from the light sensor (0-255) below which the room is considered "dark"

            InputPortSpec("hotel_card", 0), # Hotel card input port (digital)
            InputPortSpec("light_sensor_port", 5000), # Light sensor input port (analog)
            InputPortSpec("room_check_button", 0), # Room status check button inpurt port (digital)
            InputPortSpec("welcome_input_port", 0, lambda params: bool(params.get("welcome_output_port"))), # Door sensor input port (digital)

            OutputPortSpec("hotel_card_output"), # Hotel card state output port (digital)
            OutputPortSpec("power_port"), # Port to indicate whether room power should be on or off (digital)
            OutputPortSpec("do_not_disturb_port"), # DND LED output port (digital)
            OutputPortSpec("room_service_port"), # RS LED output port (digital)
            OutputPortSpec("bell_port"), # Bell activation output port (digital)
            OutputPortSpec("welcome_output_port", False, lambda params: bool(params.get("welcome_input_port"))), # Door welcome lights output port (digital)

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
            GlobalSubParamSpec("use_pullup", lambda params: params.get("card_in_state") == 0) # whether or not to use pull up resistor of all pin by default
        ])
        self.id = J.get("id", "hotel-controls")

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.card_in = 1
        self.do_not_disturb = 0
        self.room_service = 0
        self.welcome_light = 0
        self.power = 1
        self.card_out_start = -1
        self.room_check_status = 1 - self.params.get("card_in_state")
        self.door_open = 0
        self.welcome_light_start_time = 0
        self.light_sensor = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "hotel_controls"

    def sleep(self, source=None):
        super(HotelControls, self).sleep(source)
        #self.do_not_disturb = 0 # turn off DND on sleep

    def set_hardware_state(self, port, value):
        super(HotelControls, self).set_hardware_state(port, value)
        if port == self.params.get("hotel_card"):
            self.card_in = 1 if value == self.params.get("card_in_state") else 0
        elif port == self.params.get("room_check_button"):
            self.room_check_status = value
        elif port == self.params.get("welcome_input_port"):
            self.door_open = 0 if value == self.params.get("card_in_state") else 1
        elif port == self.params.get("light_sensor_port"):
            self.light_sensor = value
        return False

    def set_state(self, data, token_from="system"):
        super(HotelControls, self).set_state(data, token_from)
        if self.card_in == 1: # only respond to these if the card is inserted (so if guest leaves one on before he removes card it stays - e.g. DND)
            if "do_not_disturb" in data:
                self.do_not_disturb = int(data["do_not_disturb"])
            if "room_service" in data:
                self.room_service = int(data["room_service"])
        return False

    def update(self, cur_time_s):
        # logic for door & welcome light
        if self.door_open == 1: # if door is open and no card, turn on welcome light
            self.welcome_light = 1
            self.welcome_light_start_time = cur_time_s
        elif cur_time_s - self.welcome_light_start_time >= self.params.get("welcome_light_duration"):
            self.welcome_light = 0

        if self.card_in == 0:
            # logic for sleep
            if self.card_out_start == -1:
                self.card_out_start = cur_time_s
            elif cur_time_s - self.card_out_start > self.params.get("nocard_power_timeout"):
                self.card_out_start = cur_time_s # prevents spam commands
                self.power = 0 # turn off power
        else:
            # logic for wake-up
            if self.power == 0: # just turned on, wake Things up
                things = self.blueprint.get_things()
                for thing in things:
                    thing.wake_up(self)
            self.card_out_start = -1
            self.power = 1 # turn on power

        if self.power == 0: # force sleep everything, every update...
            things = self.blueprint.get_things()
            for thing in things:
                thing.sleep(self)
        return False

    def get_state(self):
        return {
            "card": self.card_in,
            "room_service": self.room_service,
            "do_not_disturb": self.do_not_disturb,
            "power": self.power,
        }

    def get_hardware_state(self):
        state = {}

        dnd = self.do_not_disturb
        rs = self.room_service
        if self.room_check_status == self.params.get("card_in_state"):
            dnd = 1 - self.params.get("do_not_disturb_port", "on_state")
            rs = 1 - self.params.get("room_service_port", "on_state")
            if self.card_in:
                dnd = self.params.get("do_not_disturb_port", "on_state")
            else:
                rs = self.params.get("room_service_port", "on_state")

        if self.params.get("do_not_disturb_port"):
            state[self.params.get("do_not_disturb_port")] = dnd if self.params.get("do_not_disturb_port", "on_state") == 1 else 1 - dnd

        if self.params.get("room_service_port"):
            state[self.params.get("room_service_port")] = rs if self.params.get("room_service_port", "on_state") == 1 else 1 - rs

        if self.params.get("power_port"):
            state[self.params.get("power_port")] = self.power if self.params.get("power_port", "on_state") == 1 else 1 - self.power

        # ACTIVATE bell relay if DND is on (on ACTIVE it should cut the bell circuit)
        if self.params.get("bell_port"):
            state[self.params.get("bell_port")] = self.do_not_disturb if self.params.get("bell_port", "on_state") == 1 else 1 - self.do_not_disturb

        # if welcome light output is present, set it
        if self.params.get("welcome_output_port"):
            state[self.params.get("welcome_output_port")] = self.welcome_light if self.params.get("welcome_output_port", "on_state") == 1 else 1 - self.welcome_light

        if self.params.get("hotel_card_output"):
            state[self.params.get("hotel_card_output")] = self.card_in if self.params.get("hotel_card_output", "on_state") == 1 else 1 - self.card_in

        return state

    # Used to Things (lights) when they wake-up to see if they should turn on (if room is dark)
    def is_room_dark(self):
        return self.light_sensor <= self.params.get("light_sensor_dark_threshold")
