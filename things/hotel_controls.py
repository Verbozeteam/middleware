from things.thing import Thing
from logs import Log
import json

class HotelControls(Thing):
    def __init__(self, blueprint, hotel_json):
        super(HotelControls, self).__init__(blueprint, hotel_json)
        self.input_ports[self.hotel_card] = 10000 # read card every 10 seconds
        self.output_ports[self.power_port] = 1 # digital output
        self.output_ports[self.do_not_disturb_port] = 1 # digital output
        self.output_ports[self.room_service_port] = 1 # digital output
        self.id = "hotel-controls-" + self.power_port
        self.card_in = 1
        self.do_not_disturb = 0
        self.room_service = 0
        self.power = 1
        self.power_next_update = 0
        self.card_out_start = -1

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "hotel_controls"

    def on_hardware_data(self, port, value):
        if port == self.hotel_card:
            self.card_in = value

    def on_controller_data(self, data):
        if "do_not_disturb" in data:
            self.do_not_disturb = data["do_not_disturb"]
            self.dirty = True
            self.pending_commands.append((self.do_not_disturb_port, self.do_not_disturb))
        if "room_service" in data:
            self.room_service = data["room_service"]
            self.dirty = True
            self.pending_commands.append((self.room_service_port, self.room_service))

    def update(self, cur_time_s):
        if cur_time_s >= self.power_next_update:
            self.power_next_update = cur_time_s + 5000
            if self.card_in == 0:
                if self.card_out_start == -1:
                    self.card_out_start = cur_time_s
                elif cur_time_s - self.card_out_start > self.nocard_power_timeout:
                    # turn off all Things
                    # things = self.blueprint.get_things()
                    # for thing in things:
                    #     thing.turn_off()
                    self.pending_commands.append((self.power_port, 0)) # turn off power
            else:
                self.card_out_start = -1
                self.pending_commands.append((self.power_port, 1)) # turn on power

    def get_state(self):
        return {
            "card": self.card_in,
            "room_service": self.room_service,
            "do_not_disturb": self.do_not_disturb,
            "power": self.power,
        }