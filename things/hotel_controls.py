from things.thing import Thing
from logs import Log
import json

class HotelControls(Thing):
    def __init__(self, blueprint, hotel_json):
        super(HotelControls, self).__init__(blueprint, hotel_json)
        self.input_ports[self.hotel_card] = {
            "read_interval": 0,
            "is_pullup": True,
        } # 0 means read on-change
        self.output_ports[self.power_port] = 1 # digital output
        self.output_ports[self.do_not_disturb_port] = 1 # digital output
        self.output_ports[self.room_service_port] = 1 # digital output
        self.id = "hotel-controls-" + self.power_port
        self.card_in = 1
        self.do_not_disturb = 0
        self.room_service = 0
        self.power = 1
        self.card_out_start = -1
        if not hasattr(self, "nocard_power_timeout"):
            self.nocard_power_timeout = 20
        if not hasattr(self, "card_in_state"): # card state/value that means "card is in"
            self.card_in_state = 1

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "hotel_controls"

    def sleep(self):
        super(HotelControls, self).sleep()
        self.do_not_disturb = 0 # turn off DND on sleep

    def set_hardware_state(self, port, value):
        super(HotelControls, self).set_hardware_state(port, value)
        if port == self.hotel_card:
            self.card_in = 1 if value == self.card_in_state else 0
        return False

    def set_state(self, data, token_from="system"):
        super(HotelControls, self).set_state(data, token_from)
        if "do_not_disturb" in data:
            self.do_not_disturb = int(data["do_not_disturb"])
        if "room_service" in data:
            self.room_service = int(data["room_service"])
        return False

    def update(self, cur_time_s):
        if self.card_in == 0:
            if self.card_out_start == -1:
                self.card_out_start = cur_time_s
            elif cur_time_s - self.card_out_start > self.nocard_power_timeout:
                self.card_out_start = cur_time_s # prevents spam commands
                self.power = 0 # turn off power
        else:
            if self.power == 0: # just turned on, wake Things up
                things = self.blueprint.get_things()
                for thing in things:
                    thing.wake_up()
            self.card_out_start = -1
            self.power = 1 # turn on power

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

    def get_hardware_state(self):
        return {
            self.power_port: self.power,
            self.do_not_disturb_port: self.do_not_disturb,
            self.room_service_port: self.room_service,
        }