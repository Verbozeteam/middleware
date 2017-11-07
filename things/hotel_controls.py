from things.thing import Thing
from logs import Log
import json

class HotelControls(Thing):
    def __init__(self, blueprint, hotel_json):
        super(HotelControls, self).__init__(blueprint, hotel_json)
        self.input_ports[self.hotel_card] = -1000 # read card every 1 second (negative for pullup)
        self.output_ports[self.power_port] = 1 # digital output
        self.output_ports[self.do_not_disturb_port] = 1 # digital output
        self.output_ports[self.room_service_port] = 1 # digital output
        self.id = "hotel-controls-" + self.power_port
        self.card_in = 1
        self.do_not_disturb = 0
        self.room_service = 0
        self.power = 1
        self.card_out_start = -1
        self.power_next_update = 0
        if not hasattr(self, "nocard_power_timeout"):
            self.nocard_power_timeout = 20

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "hotel_controls"

    def set_dnd(self, set_to):
        if set_to != self.do_not_disturb:
            self.do_not_disturb = set_to
            self.dirty = True
            self.pending_commands.append((self.do_not_disturb_port, self.do_not_disturb))

    def set_rs(self, set_to):
        if set_to != self.room_service:
            self.room_service = set_to
            self.dirty = True
            self.pending_commands.append((self.room_service_port, self.room_service))

    def sleep(self):
        self.set_dnd(0)

    def on_hardware_data(self, port, value):
        if port == self.hotel_card:
            self.card_in = value
            self.power_next_update = 0

    def on_controller_data(self, data):
        if "do_not_disturb" in data:
            self.set_dnd(data["do_not_disturb"])
        if "room_service" in data:
            self.set_rs(data["room_service"])

    def on_new_hardware(self):
            self.pending_commands.append((self.do_not_disturb_port, self.do_not_disturb))
            self.pending_commands.append((self.room_service_port, self.room_service))

    def update(self, cur_time_s):
        if self.card_in == 0:
            if self.card_out_start == -1:
                self.card_out_start = cur_time_s
            elif cur_time_s - self.card_out_start > self.nocard_power_timeout:
                self.card_out_start = cur_time_s # prevents spam commands
                self.power = 0
                self.pending_commands.append((self.power_port, 0)) # turn off power
        else:
            if cur_time_s >= self.power_next_update:
                if self.power == 0: # just turned on, wake Things up
                    things = self.blueprint.get_things()
                    for thing in things:
                        thing.wake_up()
                self.power_next_update = cur_time_s + 5
                self.card_out_start = -1
                self.power = 1
                self.pending_commands.append((self.power_port, 1)) # turn on power
        if self.power == 0: # force sleep everything, every update...
            things = self.blueprint.get_things()
            for thing in things:
                thing.sleep()

    def get_state(self):
        return {
            "card": self.card_in,
            "room_service": self.room_service,
            "do_not_disturb": self.do_not_disturb,
            "power": self.power,
        }