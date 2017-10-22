from things.light import Dimmer, LightSwitch
from things.curtain import Curtain
from things.air_conditioner import SplitAC, CentralAC
from things.hotel_controls import HotelControls
from things.kitchen_controls import KitchenControls
from logs import Log
from config.general_config import GENERAL_CONFIG

import json

class Room(object):
    def __init__(self, blueprint, room_json):
        self.things = {} # Thing id -> Thing dictionary
        # expected keys: "name", "grid", "detail" and "layout"
        self.config = {}
        self.config["name"] = room_json["name"]
        self.config["detail"] = room_json["detail"]
        self.config["layout"] = room_json["layout"]
        self.config["grid"] = room_json["grid"]
        for column in self.config["grid"]:
            for panel in column["panels"]:
                things = []
                for i in range(len(panel["things"])):
                    if len(panel["things"][i]) == 0: # empty space - don't load a Thing
                        panel["things"][i] = {"category": "empty"}
                    else:
                        t = blueprint.load_thing(panel["things"][i])
                        things.append(t)
                        self.things[t.id] = t
                        panel["things"][i] = {
                            "category": panel["things"][i]["category"],
                            "id": t.id,
                            "name": panel["things"][i]["name"],
                        }

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
            F = open(filename, "r", encoding="utf-8")
        except:
            Log.fatal("Cannot find blueprint file {}".format(filename))
            return
        try:
            J = json.load(F)
            F.close()
        except Exception as e:
            Log.fatal("Invalid blueprint: {}".format(str(e)))
            return

        self.rooms = [Room(self, R) for R in J]

    # Load a thing from a JSON config and append to to the given room
    # thing_json  JSON of the Thing config
    # returns     Newly loaded Thing
    def load_thing(self, thing_json):
        try:
            thing_category = thing_json["category"]
            thing_class = self.things_templates[thing_category]
        except:
            Log.error("Invalid thing category {}".format(thing_category))
            return

        try:
            return thing_class(self, thing_json)
        except:
            Log.fatal("Failed to load thing {}".format(str(thing_json)), exception=True)
            return None

    # Called when this manager needs to free all its resources
    def cleanup(self):
        pass

    # returns  The config view of the blueprint for the controller
    def get_controller_view(self):
        view = { "config": { "rooms": list(map(lambda r: r.config, self.rooms)) } }
        for room in self.rooms:
            for thing in room.things.keys():
                view[thing] = room.things[thing].get_state()
                view[thing]["category"] = room.things[thing].__class__.get_blueprint_tag()
        return view

    # returns  All things
    def get_things(self):
        ret_things = []
        for room in self.rooms:
            ret_things += list(room.things.values())
        return ret_things

    # Retrieves a Thing whose ID is given
    # thing_id  ID of the Thing
    # returns   The Thing with id thing_id, None if not found
    def get_thing(self, thing_id):
        for room in self.rooms:
            for tid in room.things.keys():
                if tid == thing_id:
                    return room.things[tid]
        return None

    # Retrieves the list of Things that are listening to a given port
    # port     Port the Thing is listening to
    # returns  List of Things listening on that port
    def get_listening_things_by_port(self, port):
        listeners = []
        for room in self.rooms:
            for thing in thing.room.things.values():
                if port in thing.input_ports or port in thing.output_ports:
                    listeners.append(thing)
        return listeners