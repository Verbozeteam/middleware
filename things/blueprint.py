from things.light import Dimmer, LightSwitch
from things.curtain import Curtain
from things.air_conditioner import SplitAC, CentralAC
from things.hotel_controls import HotelControls
from things.kitchen_controls import KitchenControls
from logs import Log
from config.general_config import GENERAL_CONFIG

import json

class Blueprint(object):
    def __init__(self, core):
        self.core = core

        # dictionary mapping tag name -> Thing class that encapsulates it
        self.things_templates = dict(map(lambda t: (t.get_blueprint_tag(), t), [
            Dimmer,
            LightSwitch,
            Curtain,
            SplitAC,
            CentralAC,
            HotelControls,
            KitchenControls,
        ]))

        filename = GENERAL_CONFIG.BLUEPRINT_FILENAME
        try:
            F = open(filename, "r")
        except:
            Log.fatal("Cannot find blueprint file {}".format(filename))
            return
        try:
            J = json.load(F)
        except Exception as e:
            Log.fatal("Invalid blueprint: {}".format(str(e)))
            return

        self.rooms = []
        for R in J:
            self.load_room(R)

    # Load a room from a JSON config and append it to self.rooms
    # room_json  JSON of the room config
    def load_room(self, room_json):
        try:
            room = {"name": room_json["name"]}
            del room_json["name"]
        except Exception as e:
            Log.error("Invalid room name in {}".format(str(room_json)))
            return

        for k in room_json.keys():
            self.load_thing(room, room_json[k], k)

        self.rooms.append(room)

    # Load a thing from a JSON config and append to to the given room
    # room              Room to append the loaded Thing to
    # thing_json        JSON of the Thing config
    # thing_class_name  Class name of the Thing being loaded
    def load_thing(self, room, thing_jsons, thing_class_name):
        try:
            thing_class = self.things_templates[thing_class_name]
        except:
            Log.error("Invalid thing type {}".format(thing_class_name))
            return

        room[thing_class_name] = []
        for thing_json in thing_jsons:
            try:
                room[thing_class_name].append(thing_class(self, thing_json))
            except:
                Log.error("Failed to load thing {}".format(str(thing_json)), exception=True)
                break

    # Called periodically by the core to update the Things of this blueprint
    # cur_time_s  current time in seconds
    def update(self, cur_time_s):
        for room in self.rooms:
            for things in room.keys():
                if things == "name":
                    continue
                for thing in room[things]:
                    if thing.dirty:
                        thing.dirty = False
                        self.broadcast_thing_state(thing)
                    thing.update(cur_time_s)
                    if len(thing.pending_commands) > 0:
                        for (port, value) in thing.get_clean_pending_commands():
                            self.core.hw_manager.on_command(port, value)
                        thing.pending_commands = []

    # Called when this manager needs to free all its resources
    def cleanup(self):
        pass

    # returns  The controller-friendly view of the blueprint
    def get_controller_view(self):
        rooms = []
        for room in self.rooms:
            obj = {}
            for things in room.keys():
                if things == "name":
                    obj["name"] = room[things]
                else:
                    obj[things] = []
                    for thing in room[things]:
                        thing_json = {"id": thing.id}
                        thing_json = {**thing_json, **thing.get_state()}
                        obj[things].append(thing_json)
            rooms.append(obj)
        return {
            "rooms": rooms,
        }

    # returns  The hardware-friendly view of the blueprint (list of things)
    def get_things(self):
        ret_things = []
        for room in self.rooms:
            for things in room.keys():
                if things == "name":
                    continue
                for thing in room[things]:
                    ret_things.append(thing)
        return ret_things

    # Called when a Thing updates its state so it broadcasts the new state
    # thing  Thing that wants to broadcast its state
    def broadcast_thing_state(self, thing):
        self.core.ctrl_manager.broadcast_thing_state(thing.id, thing.get_state())

    # Called when the hardware has an updated value on a port. This function
    # should dispatch the update to the interested Things
    # port   Port on which the update happened
    # value  New value on the given port
    def on_hardware_data(self, port, value):
        for room in self.rooms:
            for things in room.keys():
                if things == "name":
                    continue
                for thing in room[things]:
                    if port in thing.input_ports or port in thing.output_ports:
                        thing.on_hardware_data(port, value)

    # Called when the controllers send a command for a Thing
    # thing_id  id of the Thing that the controller is trying to talk to
    # data      data that the controller is sending to the Thing
    def on_controller_data(self, thing_id, data):
        Log.hammoud("Blueprint::on_controller_data({}, {})".format(thing_id, data))
        for room in self.rooms:
            for things in room.keys():
                if things == "name":
                    continue
                for thing in room[things]:
                    if thing_id == thing.id:
                        for D in data:
                            thing.on_controller_data(D)
