from things.light import LightSwitch
from logs import Log

class WaterFountain(LightSwitch):
    def __init__(self, blueprint, J):
        super(WaterFountain, self).__init__(blueprint, J)
        self.id = J.get("id", "waterfountain-" + self.params.get("switch_port"))

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "water_fountains"
