from logs import Log

class Controller(object):
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.pending_commands = []
        self.pending_state_updates = []

    def disconnect(self):
        pass

    # Called when the controller receives a command
    # json_command  A JSON-serializable dictionary that represents the command
    def on_command(self, json_command):
        self.pending_commands.append(json_command)

    # Called by the manager when a Thing has a state update for this controller
    # thing_id  id of the Thing
    # state     New state of the the Thing
    def on_thing_state(self, thing_id, state):
        self.pending_state_updates.append((thing_id, state))

    # Called when the controller has pending bytes to read
    def on_read_data(self):
        pass

    # Called when data needs to be sent to the remote controller
    def on_send_data(self, json_data):
        pass
