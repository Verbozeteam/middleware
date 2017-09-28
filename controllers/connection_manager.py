from logs import Log

#
# Base class for a connection manager
# A connection manager is responsible for managing controllers connecting
# using a certain method (e.g. socket IO, Http server, etc...)
#
class ConnectionManager(object):
    def __init__(self, controllers_manager):
        self.controllers_manager = controllers_manager
        self.connected_controllers = []

    # For every connected controller:
    # - Writes out the state updates
    # - Reads in the commands and sends them to their respective Things
    # cur_time_s  Current system time in seconds
    def update(self, cur_time_s):
        controllers = self.connected_controllers
        for controller in controllers:
            # pending updates to be written to the controller
            if len(controller.pending_state_updates) > 0:
                big_update = {}
                for (thing_id, state) in controller.pending_state_updates:
                    big_update[thing_id] = state
                controller.pending_state_updates = []
                if not controller.on_send_data(big_update):
                    self.disconnect_controller(controller)
            # pending commands read from the controller
            if len(controller.pending_commands) > 0:
                collected_commands = {}
                control_commands = []
                for command in controller.pending_commands:
                    if "thing" in command:
                        thing_id = command["thing"]
                        del command["thing"]
                        if thing_id in collected_commands:
                            collected_commands[thing_id].append(command)
                        else:
                            collected_commands[thing_id] = [command]
                    else:
                        control_commands.append(command)
                controller.pending_commands = []
                for thing_id in collected_commands.keys():
                    commands = collected_commands[thing_id]
                    self.controllers_manager.send_thing_commands(thing_id, commands)
                for command in control_commands:
                    self.controllers_manager.send_control_command(controller, command)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        for controller in self.connected_controllers:
            controller.disconnect()
        self.connected_controllers = []

    # Registers a controller as connected
    # controller  A Controller object that is connected
    def register_controller(self, controller):
        Log.info("Controller connected: {}".format(str(controller)))
        self.connected_controllers.append(controller)

    # Disconnects a controller and calls .disconnect() on it
    # controller  The controller to disconnect
    def disconnect_controller(self, controller):
        for c in self.connected_controllers:
            if c == controller:
                self.connected_controllers.remove(c)
                break
        controller.disconnect()
        Log.info("Controller disconnected: {}".format(str(controller)))

    # Broadcasts the state of a Thing to all connected controllers
    def broadcast_thing_state(self, thing_id, state):
        for C in self.connected_controllers:
            C.on_thing_state(thing_id, state)
