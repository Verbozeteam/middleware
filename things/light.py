from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, blueprint, light_json):
        super(LightSwitch, self).__init__(blueprint, light_json)
        self.output_ports[self.switch_port] = 1 # digital output
        self.id = light_json.get("id", "lightswitch-" + self.switch_port)
        self.intensity = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "light_switches"

    def set_intensity(self, intensity):
        self.intensity = int(min(max(intensity, 0), 1))
        self.dirty = True
        self.pending_commands.append((self.switch_port, self.intensity))

    def sleep(self):
        self.saved_wakeup_value = self.intensity
        if self.intensity == 1:
            self.set_intensity(0)

    def wake_up(self):
        if hasattr(self, "default_wakeup_value"):
            self.set_intensity(self.default_wakeup_value)
        elif hasattr(self, "saved_wakeup_value"):
            self.set_intensity(self.saved_wakeup_value)

    def on_new_hardware(self):
        self.set_intensity(self.intensity)

    def on_controller_data(self, data):
        if "intensity" in data:
            self.set_intensity(data["intensity"])

    def get_state(self):
        return {
            "intensity": self.intensity
        }

class Dimmer(Thing):
    def __init__(self, blueprint, dimmer_json):
        super(Dimmer, self).__init__(blueprint, dimmer_json)
        self.output_ports[self.dimmer_port] = 2 # pwm output
        self.is_isr_dimmer = "v" in self.dimmer_port # if dimmer_port is a virtual port then this is an ISR light
        self.id = "dimmer-" + self.dimmer_port
        self.intensity = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dimmers"

    def set_intensity(self, intensity):
        self.intensity = int(min(max(intensity, 0), 100))
        self.dirty = True
        if self.is_isr_dimmer:
            # light_power = int(self.intensity) # 0-100
            # if light_power > 100: light_power = 100
            # if light_power < 5: light_power = 0
            # light_power = 100 - (light_power/2) # 50-100

            light_power = int(min(max(100.0 - (float(self.intensity) / 1.3), 25.0), 100.0))
            if light_power > 85 and light_power < 97:
                light_power = 85
            elif light_power >= 97:
                light_power = 105 # so that zero-crossing has no way of nakba
            self.pending_commands.append((self.dimmer_port, int(light_power)))
        else:
            self.pending_commands.append((self.dimmer_port, int(self.intensity * 2.55)))

    def sleep(self):
        self.saved_wakeup_value = self.intensity
        if self.intensity > 0:
            self.set_intensity(0)

    def wake_up(self):
        if hasattr(self, "default_wakeup_value"):
            self.set_intensity(self.default_wakeup_value)
        elif hasattr(self, "saved_wakeup_value"):
            self.set_intensity(self.saved_wakeup_value)

    def on_new_hardware(self):
        self.set_intensity(self.intensity)

    def on_controller_data(self, data):
        if "intensity" in data:
            self.set_intensity(data["intensity"])

    def get_state(self):
        return {
            "intensity": self.intensity
        }
