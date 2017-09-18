from things.light import Dimmer, LightSwitch
from things.curtain import Curtain
from logs import Log

import json

class Blueprint(object):
    def __init__(self, filename):
        # dictionary mapping tag name -> Thing class that encapsulates it
        self.things = dict(map(lambda t: (t.get_blueprint_tag(), t), [
            Dimmer,
            LightSwitch,
            Curtain
        ]))

        try:
            F = open(filename, "r")
        except:
            Log.error("Cannot find blueprint file {}".format(filename))
            return
        try:
            J = json.load(F)
        except Exception as e:
            Log.error("Invalid blueprint: {}".format(str(e)))
            return

        self.rooms = []
        for R in J:
            self.load_room(R)

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

    def load_thing(self, room, thing_jsons, thing_class_name):
        try:
            thing_class = self.things[thing_class_name]
        except:
            Log.error("Invalid thing type {}".format(thing_class_name))
            return

        room[thing_class_name] = []
        for thing_json in thing_jsons:
            try:
                room[thing_class_name].append(thing_class(thing_json))
            except:
                Log.error("Failed to load thing {}".format(str(thing_json)))
                break

    def get_display_view(self):
        pass

