from logs import Log

class Thing(object):
    def __init__(self, blueprint, thing_json):
        # Read Thing attributes
        for key in thing_json.keys():
            setattr(self, key, thing_json[key])

        # auto-generated attributes
        self.blueprint = blueprint
        self.input_ports = {}                   # Dictionary of pin -> read_interval where pin is a pin that the Thing wants to listen to and read_interval is an integer for the interval at which the port is read (in ms)
        self.output_ports = {}                  # Dictionary of pin -> output type (0 for digital, 1 for PWM)
        self.dirty = False                      # If True, then this Thing's state has changed since it was last broadcasted to controllers
        self.pending_commands = []              # List of pending messages to be sent to the hardware
        self.allow_duplicate_commands = False   # If set to False, commands will be truncated in get_clean_pending_commands() if they target the same port
        self.id = ""                            # id of this Thing

    # Should be implemented to return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return ""

    # Should be implemented to return the state of this Thing that will be sent to controllers (JSON-serializable dictionary)
    def get_state(self):
        return {}

    # Should be implemented to order this Thing to go to sleep (usually turn off)
    def sleep(self):
        pass

    # Should be implemented to order this Thing wake up (usually turn on)
    def wake_up(self):
        pass

    # perform any Thing-specific logic
    # cur_time_s  Current time in seconds
    def update(self, cur_time_s):
        pass

    # Retrieves the pending commands (form controllers)
    # return  A (cleaned) list of pending commands
    def get_clean_pending_commands(self):
        # if pending commands are allowed to duplicate, just return all pending_commands
        if self.allow_duplicate_commands:
            return self.pending_commands

        commands = []
        added_ports = []
        for command in self.pending_commands:
            if command[0] not in added_ports:
                added_ports.append(command[0])
                commands = [command] + commands
        return commands

    # Called by the blueprint when hardware has an updated value on a port
    # port   Port that has updated its value
    # value  New value on that port
    def on_hardware_data(self, port, value):
        pass

    # Called by the blueprint when a controller sends a message
    # data  Message sent by the controller
    def on_controller_data(self, data):
        pass

