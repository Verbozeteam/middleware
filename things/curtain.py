from things.thing import Thing
from logs import Log
import json

class Curtain(Thing):
    def __init__(self, curtain_json):
        pass

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "curtains"
