from logs import Log

class Thing(object):
    def __init__(self):
        self.listening_ports = []
        self.dirty = False
        self.id = ""

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

