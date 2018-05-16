from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from logs import Log
import json

class LightSwitch(Thing):
    def __init__(self, blueprint, J):
        super(LightSwitch, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("default_wakeup_value"), # Default value when awoken

            OutputPortSpec("switch_port", is_required=True), # Switch outport port

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
        ])
        self.id = J.get("id", "lightswitch-" + str(self.params.get("switch_port")))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.intensity = 0

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
            if self.params.get("default_wakeup_value") != None:
                self.set_intensity(self.params.get("default_wakeup_value"))
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
        if type(self.params.get("switch_port")) != type([]):
            state[self.params.get("switch_port")] = self.intensity if self.params.get("switch_port", "on_state") == 1 else 1 - self.intensity
        else: # array of output ports
            for sp in self.params.get("switch_port"):
                state[sp] = self.intensity if self.params.get("switch_port", "on_state") == 1 else 1 - self.intensity

        return state

class Dimmer(Thing):
    def __init__(self, blueprint, J):
        super(Dimmer, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            ParamSpec("default_wakeup_value"), # Default value when awoken
            ParamSpec("max_output_percentage", 80), # Maxmimum output percentage
            ParamSpec("has_switch", 0), # 0 if the dimmer has no switch button, 1 otherwise

            OutputPortSpec(["dimmer_port", "dimmer_ports"], is_pwm=True, is_required=True), # Dimmer outport port

            GlobalSubParamSpec("on_state", 1), # Default on-state for all ports: on-state is the state when the port is considered ACTIVE (1 means HIGH when active, 0 means LOW when active)
        ])
        self.id = J.get("id", "dimmer-" + str(self.params.get("dimmer_port")))

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        check_isr_ports = self.params.get("dimmer_port")
        if type(check_isr_ports) == type([]): check_isr_ports = check_isr_ports[0]
        self.is_isr_dimmer = "v" in check_isr_ports # if dimmer_port is a virtual port then this is an ISR light
        self.intensity = 0

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
            if self.params.get("default_wakeup_value") != None:
                self.set_intensity(self.params.get("default_wakeup_value"))
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
        ports = self.params.get("dimmer_port")
        if type(ports) != type([]):
            ports = [ports]

        if self.is_isr_dimmer:
            light_power = int(min(max(100.0 - (float(self.intensity) * (self.params.get("max_output_percentage")/100.0)), 100.0-self.params.get("max_output_percentage")), 100.0))
            if self.virtual_port_data[0][0] == 1: # old ISR needs some regulation
                if light_power > 85 and light_power < 97:
                    light_power = 85
                elif light_power >= 97:
                    light_power = 105 # so that zero-crossing has no way of nakba

        state = {}
        for port in ports:
            state[port] = int(light_power)
        return state

    def get_metadata(self):
        return {
            "has_switch": self.params.get("has_switch"),
        }

