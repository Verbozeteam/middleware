from things.light import LightSwitch
from logs import Log

class WaterFountain(LightSwitch):
    def __init__(self, blueprint, light_json):
        super(WaterFountain, self).__init__(blueprint, light_json)
        self.id = light_json.get("id", "waterfountain-" + self.switch_port)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "water_fountains"