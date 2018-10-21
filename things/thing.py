from logs import Log
from functools import reduce
import itertools

class Thing(object):
    def __init__(self, blueprint, thing_json):
        # auto-generated attributes
        self.blueprint = blueprint
        self.id = ""                            # id of this Thing
        self.name = thing_json["name"]          # name of this Thing
        self.last_change_token = ""             # token from the controller who last changed the state

        self.input_ports = {}                   # Dictionary of pin -> {"read_interval": (int), "is_pullup": (bool)}
                                                # OR            pin -> read_interval (int)
                                                # pin: pin that the Thing wants to listen to
                                                # read_interval: is an integer for the interval at which the port is read (in ms)
                                                # is_pullup (optional): indicates whether or not to use a pullup resistor

        self.output_ports = {}                  # Dictionary of pin -> output type (0 for digital, 1 for PWM)
        self.virtual_port_data = thing_json.get("virtual_port_data", [])

    # Should be implemented to return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return ""

    # Should be implemented to return the state of this Thing that will be sent to controllers (JSON-serializable dictionary)
    def get_state(self):
        return {}

    # Should be implemented to return the state of this Thing that will be sent to hardware (dictionary of port -> value)
    def get_hardware_state(self):
        return {}

    # Should be implemented to order this Thing to go to sleep (usually turn off)
    # source  The Thing that caused the sleep to happen. Could be None to indicate "system"
    def sleep(self, source=None):
        self.last_change_token = "system"
        pass

    # Should be implemented to order this Thing wake up (usually turn on)
    # source  The Thing that caused the wake-up to happen. Could be None to indicate "system"
    def wake_up(self, source=None):
        self.last_change_token = "system"
        pass

    # perform any Thing-specific logic
    # cur_time_s  Current time in seconds
    # returns     returns whether or not another updated is required ASAP after a
    #             select cycle
    def update(self, cur_time_s):
        return False

    # Called by the blueprint when hardware has an updated value on a port
    # port     Port that has updated its value
    # value    New value on that port
    # returns  True iff the changes made to the state are more than just the input
    def set_hardware_state(self, port, value):
        self.last_change_token = "system"
        return True

    # Called by the blueprint when a controller sends a message
    # data       Message sent by the controller
    # token_from A token to identify the source of the command to set state
    # returns    XXX True iff the changes made to the state are more than just the input (DEPRICATED)
    def set_state(self, data, token_from="system"):
        self.last_change_token = token_from
        return True

    # Called by the blueprint ONCE (at the beginning) to know if there is any metadata for this Thing
    # returns  A dictionary of metadata ammended to the Thing in the config in the blueprint
    def get_metadata(self):
        return {}


class ParamSpec(object):
    def __init__(self, pname, default=None, is_required=False):
        if type(pname) == type(""):
            self.name = pname
            self.namelist = [pname]
        else:
            self.name = pname[0]
            self.namelist = pname
        self.default = default
        self.is_required = is_required

    def apply(self, thing_params, j):
        # if name was an array, make sure we pick one that exists in j (as much as we can)
        jname = self.name
        for N in self.namelist:
            if N in j:
                jname = N
        default = self.default if type(self.default) != type(lambda: None) else self.default(thing_params)
        thing_params.params[self.name] = ParamValue(self.name, j.get(jname, default))
        is_required = self.is_required if type(self.is_required) != type(lambda: None) else self.is_required(thing_params)
        if is_required and not thing_params.params.get(self.name):
            Log.fatal('required parameter is missing: {}'.format(self.name))

    def apply_atend(self, thing_params, j):
        pass

class InputPortSpec(ParamSpec):
    def __init__(self, pname, read_interval, is_required=False):
        super(InputPortSpec, self).__init__(pname, None, is_required)
        self.read_interval = read_interval

    def apply(self, thing_params, j):
        super(InputPortSpec, self).apply(thing_params, j)

    def apply_atend(self, thing_params, j):
        super(InputPortSpec, self).apply_atend(thing_params, j)
        port = thing_params.get(self.name)
        if port:
            p_desc = {
                "read_interval": self.read_interval,
                "is_pullup": bool(thing_params.get(self.name, "use_pullup"))
            }
            if type(port) != type([]):
                thing_params.input_ports[port] = p_desc["read_interval"] if port[0] == "v" else p_desc # virtual ports don't use pullups
            else:
                for p in port:
                    thing_params.input_ports[p] = p_desc["read_interval"] if p[0] == "v" else p_desc # virtual ports don't use pullups

class OutputPortSpec(ParamSpec):
    def __init__(self, pname, is_pwm=False, is_required=False):
        super(OutputPortSpec, self).__init__(pname, None, is_required)
        self.is_pwm = is_pwm

    def apply(self, thing_params, j):
        super(OutputPortSpec, self).apply(thing_params, j)
        port = thing_params.get(self.name)
        if port:
            if type(port) != type([]):
                thing_params.output_ports[port] = 1 if not self.is_pwm else 2
            else:
                for p in port:
                    thing_params.output_ports[p] = 1 if not self.is_pwm else 2

class GlobalSubParamSpec(ParamSpec):
    def __init__(self, pname, default, is_required=False):
        super(GlobalSubParamSpec, self).__init__(pname, default, is_required)

    def apply(self, thing_params, j):
        super(GlobalSubParamSpec, self).apply(thing_params, j)
        default = self.default if type(self.default) != type(lambda: None) else self.default(thing_params)
        for p in thing_params.params.keys():
            thing_params.params[p].sub_param_values[self.name] = j.get(p+"_"+self.name, j.get(self.name, default))

class ParamValue(object):
    def __init__(self, pname, value):
        self.pname = pname
        self.value = value
        self.sub_param_values = {}

class ThingParams(object):
    def __init__(self, j, spec):
        self.params = {}
        self.input_ports = {}
        self.output_ports = {}
        sub_param_specs_names = list(itertools.chain.from_iterable(map(lambda gsp: gsp.namelist, filter(lambda s: isinstance(s, GlobalSubParamSpec), spec))))
        for s in spec:
            s.apply(self, j) # let the spec object apply itself on the parameters
        for s in spec:
            s.apply_atend(self, j) # let the spec object apply itself on the parameters
        for k in j.keys():
            if k not in ["id", "name", "category", "virtual_port_data"] + list(self.params.keys()) and not reduce(lambda a,b: a or b, map(lambda spn: k.endswith(spn), sub_param_specs_names), False):
                Log.warning("Unknown parameter: {}".format(k))

    def get(self, name, postfix=None):
        if not name in self.params:
            return None
        if postfix != None and postfix not in self.params[name].sub_param_values:
            if postfix not in self.params:
                return None
            return self.params[postfix].value
        return self.params[name].value if postfix == None else self.params[name].sub_param_values[postfix]

    def get_input_ports(self):
        return self.input_ports

    def get_output_ports(self):
        return self.output_ports

