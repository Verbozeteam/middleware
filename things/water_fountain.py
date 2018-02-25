from things.thing import Thing
from logs import Log

class WaterFountain(Thing):
    def __init__(self, blueprint, light_json):
        super(WaterFountain, self).__init__(blueprint, light_json)
        self.output_ports[self.switch_port] = 1 # digital output
        self.id = light_json.get("id", "waterfountain-" + self.switch_port)
        self.output = 0
        if not hasattr(self, "on_state"):
            self.on_state = 1

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "water_fountains"

    def set_output(self, output):
        self.output = int(min(max(output, 0), 1))

    def sleep(self):
        super(WaterFountain, self).sleep()
        if not hasattr(self, "saved_wakeup_value"):
            self.saved_wakeup_value = self.output

        if self.output == 1:
            self.set_output(0)

    def wake_up(self):
        super(WaterFountain, self).wake_up()
        if hasattr(self, "default_wakeup_value"):
            self.set_output(self.default_wakeup_value)
        elif hasattr(self, "saved_wakeup_value"):
            self.set_output(self.saved_wakeup_value)

        if hasattr(self, "saved_wakeup_value"):
            delattr(self, "saved_wakeup_value")

    def set_state(self, data, token_from="system"):
        super(WaterFountain, self).set_state(data, token_from)
        if hasattr(self, "saved_wakeup_value"):
            return # block updates while sleeping

        if "output" in data:
            self.set_output(data["output"])
        return False

    def get_state(self):
        return {
            "output": self.output
        }

    def get_hardware_state(self):
        return {
            self.switch_port: self.output if self.on_state == 1 else 1 - self.output,
        }