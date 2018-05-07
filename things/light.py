from things.thing import Thing
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, blueprint, light_json):
        super(LightSwitch, self).__init__(blueprint, light_json)
        if type(self.switch_port) == type(""):
            switch_port_str = self.switch_port
            self.output_ports[self.switch_port] = 1 # digital output
        else: # array of output ports
            switch_port_str = self.switch_port[0]
            for sp in self.switch_port:
                self.output_ports[sp] = 1 # digital output
        self.id = light_json.get("id", "lightswitch-" + switch_port_str)
        self.intensity = 0
        if not hasattr(self, "on_state"):
            self.on_state = 1

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "light_switches"

    def set_intensity(self, intensity):
        self.intensity = int(min(max(intensity, 0), 1))

    def sleep(self, source=None):
        super(LightSwitch, self).sleep(source)
        if not hasattr(self, "saved_wakeup_value"):
            self.saved_wakeup_value = self.intensity

        if self.intensity == 1:
            self.set_intensity(0)

    def wake_up(self, source=None):
        super(LightSwitch, self).wake_up(source)
        should_turn_on = True
        if source and hasattr(source, "is_room_dark") and source.is_room_dark() == False:
            should_turn_on = False
        if should_turn_on:
            if hasattr(self, "default_wakeup_value"):
                self.set_intensity(self.default_wakeup_value)
            elif hasattr(self, "saved_wakeup_value"):
                self.set_intensity(self.saved_wakeup_value)

        if hasattr(self, "saved_wakeup_value"):
            delattr(self, "saved_wakeup_value")

    def set_state(self, data, token_from="system"):
        super(LightSwitch, self).set_state(data, token_from)
        if hasattr(self, "saved_wakeup_value"):
            return # block updates while sleeping

        if "intensity" in data:
            self.set_intensity(data["intensity"])
        return False

    def get_state(self):
        return {
            "intensity": self.intensity
        }

    def get_hardware_state(self):
        state = {}
        if type(self.switch_port) == type(""):
            state[self.switch_port] = self.intensity if self.on_state == 1 else 1 - self.intensity
        else: # array of output ports
            for sp in self.switch_port:
                state[sp] = self.intensity if self.on_state == 1 else 1 - self.intensity

        return state

class Dimmer(Thing):
    def __init__(self, blueprint, dimmer_json):
        super(Dimmer, self).__init__(blueprint, dimmer_json)
        if hasattr(self, "dimmer_port"):
            self.dimmer_ports = [self.dimmer_port]
        else:
            self.dimmer_port = self.dimmer_ports[0]
        for port in self.dimmer_ports:
            self.output_ports[port] = 2 # pwm output
        self.is_isr_dimmer = "v" in self.dimmer_port # if dimmer_port is a virtual port then this is an ISR light
        self.id = dimmer_json.get("id", "dimmer-" + self.dimmer_port)
        self.intensity = 0

        if not hasattr(self, "max_output_percentage"):
            self.max_output_percentage = 80
        if not hasattr(self, "has_switch"):
            self.has_switch = 0

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "dimmers"

    def set_intensity(self, intensity):
        self.intensity = int(min(max(intensity, 0), 100))

    def sleep(self, source=None):
        super(Dimmer, self).sleep(source)
        if not hasattr(self, "saved_wakeup_value"):
            self.saved_wakeup_value = self.intensity

        if self.intensity > 0:
            self.set_intensity(0)

    def wake_up(self, source=None):
        super(Dimmer, self).wake_up(source)
        should_turn_on = True
        if source and hasattr(source, "is_room_dark") and source.is_room_dark() == False:
            should_turn_on = False
        if should_turn_on:
            if hasattr(self, "default_wakeup_value"):
                self.set_intensity(self.default_wakeup_value)
            elif hasattr(self, "saved_wakeup_value"):
                self.set_intensity(self.saved_wakeup_value)

        if hasattr(self, "saved_wakeup_value"):
            delattr(self, "saved_wakeup_value")

    def set_state(self, data, token_from="system"):
        super(Dimmer, self).set_state(data, token_from)
        if hasattr(self, "saved_wakeup_value"):
            return # block updates while sleeping

        if "intensity" in data:
            self.set_intensity(data["intensity"])
        return False

    def get_state(self):
        return {
            "intensity": self.intensity,
        }

    def get_hardware_state(self):
        light_power = int(self.intensity * 2.55)

        if self.is_isr_dimmer:
            light_power = int(min(max(100.0 - (float(self.intensity) * (self.max_output_percentage/100.0)), 100.0-self.max_output_percentage), 100.0))
            if self.virtual_port_data[0][0] == 1: # old ISR needs some regulation
                if light_power > 85 and light_power < 97:
                    light_power = 85
                elif light_power >= 97:
                    light_power = 105 # so that zero-crossing has no way of nakba

        state = {}
        for port in self.dimmer_ports:
            state[port] = int(light_power)
        return state

    def get_metadata(self):
        return {
            "has_switch": self.has_switch,
        }

