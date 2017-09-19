from logs import Log

class Thing(object):
    def __init__(self):
        self.listening_ports = []   # List of ports that this Thing is listening for changes on
        self.dirty = False          # If True, then this Thing's state has changed since it was last broadcasted to controllers
        self.pending_commands = []  # List of pending messages to be sent to the hardware
        self.id = ""                # id of this Thing

    # Should be implemented to return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return ""

    # Should be implemented to return the state of this Thing that will be sent to controllers (JSON-serializable dictionary)
    def get_state(self):
        return {}

    # Called by the blueprint when hardware has an updated value on a port
    # port   Port that has updated its value
    # value  New value on that port
    def on_hardware_data(self, port, value):
        pass

    # Called by the blueprint when a controller sends a message
    # data  Message sent by the controller
    def on_controller_data(self, data):
        pass

