from logs import Log

class Thing(object):
    def __init__(self, blueprint, thing_json):
        # Read Thing attributes
        for key in thing_json.keys():
            setattr(self, key, thing_json[key])

        # auto-generated attributes
        self.blueprint = blueprint
        self.id = ""                            # id of this Thing
        self.last_change_token = ""             # token from the controller who last changed the state

        self.input_ports = {}                   # Dictionary of pin -> {"read_interval": (int), "is_pullup": (bool)}
                                                # OR            pin -> read_interval (int)
                                                # pin: pin that the Thing wants to listen to
                                                # read_interval: is an integer for the interval at which the port is read (in ms)
                                                # is_pullup (optional): indicates whether or not to use a pullup resistor

        self.output_ports = {}                  # Dictionary of pin -> output type (0 for digital, 1 for PWM)


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
    def sleep(self):
        self.last_change_token = "system"
        pass

    # Should be implemented to order this Thing wake up (usually turn on)
    def wake_up(self):
        self.last_change_token = "system"
        pass

    # perform any Thing-specific logic
    # cur_time_s  Current time in seconds
    def update(self, cur_time_s):
        pass

    # Called by the blueprint when hardware has an updated value on a port
    # port     Port that has updated its value
    # value    New value on that port
    # returns  True iff the changes made to the state are more than just the input
    def set_hardware_state(self, port, value):
        self.last_change_token = "system"
        return True

    # Called by the blueprint when a controller sends a message
    # data       Message sent by the controller
    # token_from
    # returns    True iff the changes made to the state are more than just the input
    def set_state(self, data, token_from="system"):
        self.last_change_token = token_from
        return True

    # Called by the blueprint ONCE (at the beginning) to know if there is any metadata for this Thing
    # returns  A dictionary of metadata ammended to the Thing in the config in the blueprint
    def get_metadata(self):
        return {}

