from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, blueprint, light_json):
        super(LightSwitch, self).__init__(blueprint, light_json)
        self.output_ports[self.switch_port] = 1 # digital output
        self.id = "lightswitch-" + self.switch_port
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
            self.pending_commands.append((self.dimmer_port, int((float(self.intensity) / 100.0) * (self.virtual_port_data[0][1]-1))))
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
