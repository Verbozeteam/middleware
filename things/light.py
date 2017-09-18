from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, light_json):
        pass

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "light_switches"

class Dimmer(Thing):
    def __init__(self, dimmer_json):
        pass

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dimmers"
