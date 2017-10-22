from logs import Log
from controllers.tcp_socket_controllers import TCPSocketConnectionManager

from functools import reduce

class CONTROL_CODES:
    GET_BLUEPRINT = 0
    GET_THING_STATE = 1
    SET_LISTENERS = 2

#
# Controllers manager is responsible for all interaction with controller
# devices (tablets, phones, etc...)
#
class ControllersManager(object):
    def __init__(self, core):
        self.core = core
        self.connected_controllers = []
        self.tcp_socket_connection_manager = TCPSocketConnectionManager(self)
        self.connection_managers = [
            self.tcp_socket_connection_manager,
        ]

    # Registers a controller
    # controller  A Controller object that is connected
    def register_controller(self, controller):
        self.connected_controllers.append(controller)

    # Disconnects a controller and calls .disconnect() on it
    # controller  The controller to disconnect
    def deregister_controller(self, controller):
        for c in self.connected_controllers:
            if c == controller:
                self.connected_controllers.remove(c)
                break

    # called to periodically update this manager
    # cur_time_s  current time in seconds
    def update(self, cur_time_s):
        for C in self.connection_managers:
            C.update(cur_time_s)

        for controller in list(self.connected_controllers):
            try:
                keep = controller.update(cur_time_s)
            except:
                keep = False
            if not keep:
                controller.destroy_selectible()

    # Called when this manager needs to free all its resources
    def cleanup(self):
        for controller in self.connected_controllers:
            controller.destroy_selectible()
        for C in self.connection_managers:
            C.cleanup()

    # Called when a controller sends a control command
    # controller  Controller that sent the command
    # command     JSON control command sent
    def on_control_command(self, controller, command):
        if "code" in command:
            Log.debug("ControllersManager::on_control_command({}, {})".format(str(controller), command))
            try:
                if command["code"] == CONTROL_CODES.GET_BLUEPRINT:
                    controller.send_data(self.core.blueprint.get_controller_view(), cache=False)
                elif command["code"] == CONTROL_CODES.GET_THING_STATE:
                    controller.invalidate_cache(thing_id=command.get("thing-id", None))
                elif command["code"] == CONTROL_CODES.SET_LISTENERS:
                    listeners = command.get("things", None)
                    if listeners and type(listeners) is list and reduce(lambda l1, l2: l1 and l2, map(lambda s: type(s) is str, listeners)):
                        controller.things_listening = listeners
            except:
                Log.error("Failed to respond to a control command", exception=True)
                pass
