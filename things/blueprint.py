from things.light import Dimmer, LightSwitch
from things.curtain import Curtain
from things.air_conditioner import SplitAC, CentralAC
from things.hotel_controls import HotelControls
from things.kitchen_controls import KitchenControls
from things.water_fountain import WaterFountain
from logs import Log
from config.general_config import GENERAL_CONFIG

import json

class RemoteBoard(object):
    def __init__(self, address, board_json):
        self.address = address
        self.digital_port_start_range = board_json.get("digital_port_start_range", 0)
        self.num_digital_ports = board_json.get("num_digital_ports", 53)
        self.analog_port_start_range = board_json.get("analog_port_start_range", 0)
        self.num_analog_ports = board_json.get("num_analog_ports", 16)
        self.virtual_port_start_range = board_json.get("virtual_port_start_range", 0)
        self.num_virtual_ports = board_json.get("num_virtual_ports", 8)

class Room(object):
    def __init__(self, blueprint, room_json):
        self.things = {} # Thing id -> Thing dictionary
        self.things_meta = {} # Thing id -> Thing metadata dictionary (metadata is category/id/name (created below))

        # expected keys: "name", "id" and "groups"
        self.config = {}
        self.config["name"] = room_json["name"]
        self.config["id"] = room_json["id"]
        self.config["groups"] = json.loads(json.dumps(room_json["groups"]))

        if type(self.config["id"]) != type(str()):
            raise ("Room id type not string: " + str(self.config))

        found_groups = {}
        for group in self.config["groups"]:
            if "id" not in group:
                raise ("Missing group id: " + str(group))
            if type(group["id"]) != type(str()):
                raise ("Group id type not string: " + str(group))
            if group["id"] in found_groups:
                raise ("Duplicated group id: " + group["id"])
            found_groups[group["id"]] = 1
            for i in range(len(group["things"])):
                if len(group["things"][i]) == 0: # empty space - don't load a Thing
                    group["things"][i] = {"category": "empty"}
                elif len(group["things"][i]) > 1: # ignore the ones with only one key - they are references to other Things
                    t = blueprint.load_thing(group["things"][i])
                    self.things[t.id] = t
                    name = group["things"][i]["name"]
                    category = group["things"][i]["category"]
                    group["things"][i] = t.get_metadata()
                    group["things"][i]["category"] = category
                    group["things"][i]["id"] = t.id
                    group["things"][i]["name"] = name

    # Loads the references (Things in the config with only 1 key "id") to be copies of what they refer to
    def load_references(self, blueprint):
        for group in self.config["groups"]:
            for i in range(len(group["things"])):
                thing = group["things"][i]
                if len(thing) == 1 and "id" in thing:
                    group["things"][i] = blueprint.get_thing_metadata(thing["id"])
                    if thing == None:
                        raise ("Failed to find reference to " + thing["id"])

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
            WaterFountain,
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

        self.id = str(J["id"])
        self.translations = J.get("translations", {})
        self.rooms = [Room(self, R) for R in J["rooms"]]
        found_room_ids = {}
        for R in self.rooms:
            if R.config["id"] in found_room_ids:
                raise ("Dumplicate room id" + R.config["id"])
            found_room_ids[R.config["id"]] = 1
            R.load_references(self)
        remote_boards_data = J.get("remote_boards", {"": {}})
        self.remote_boards = {}
        for key in remote_boards_data.keys():
            self.remote_boards[key] = RemoteBoard(key, remote_boards_data[key])

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
        view = {
            "config": {
                "translations": self.translations,
                "rooms": list(map(lambda r: r.config, self.rooms)),
                "id": str(self.id)
            }
        }
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
            if thing_id in room.things:
                return room.things[thing_id]
        return None

    # Retrieves the Thing object that is stored in the config (name, category and id)
    # thing_id  ID of the Thing to look for
    # returns   {name, category, id} of the found Thing
    def get_thing_metadata(self, thing_id):
        for room in self.rooms:
            if thing_id in room.things_meta:
                return room.things_meta[thing_id]
        return None

    # Retrieves the list of Things that are listening to a given port
    # port     Port the Thing is listening to
    # returns  List of Things listening on that port
    def get_listening_things_by_port(self, port):
        listeners = []
        for room in self.rooms:
            for thing in room.things.values():
                if port in thing.input_ports or port in thing.output_ports:
                    listeners.append(thing)
        return listeners

    # Retrieves a RemoteBoard object for a given board address
    # address  64 bit address of a Zigbee (number)
    # returns  A RemoteBoard object corresponding to that address, or None if not defined
    def get_remote_board(self, address):
        address = "%x" % address
        if address in self.remote_boards:
            return self.remote_boards[address]
        return None
