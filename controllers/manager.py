from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG
from controllers.tcp_socket_controllers import TCPSocketConnectionManager, TCPSSLSocketConnectionManager
from controllers.authentication import ControllerAuthentication

from functools import reduce

class CONTROL_CODES:
    GET_BLUEPRINT = 0       # Ask for the blueprint
    GET_THING_STATE = 1     # Ask for the state of a specific Thing
    SET_LISTENERS = 2       # Set which Things to listen to updates from
    RESET_QRCODE = 3        # Request QR code to be reset (sent by controllers)
    SET_QRCODE = 4          # Set the QR code (sent by a Hub)

#
# Controllers manager is responsible for all interaction with controller
# devices (tablets, phones, etc...)
#
class ControllersManager(object):
    def __init__(self, core):
        self.core = core
        self.connected_controllers = {} # origin_name -> list of connected controllers from that origin
        self.connection_managers = [
            TCPSocketConnectionManager(self),
            TCPSSLSocketConnectionManager(self),
        ]
        ControllerAuthentication.initialize()

    # Checks if a connection from the given origin is allowed
    def can_connect_from_origin(self, origin):
        return \
            (origin not in self.connected_controllers or len(self.connected_controllers[origin]) < CONTROLLERS_CONFIG.MAX_CONNECTIONS_PER_ORIGIN) and \
            reduce(lambda a, b: a+b, map(lambda cc: len(cc), self.connected_controllers.values()), 0) < CONTROLLERS_CONFIG.MAX_CONNECTIONS

    # Registers a controller
    # controller  A Controller object that is connected
    def register_controller(self, controller):
        if controller.origin_name in self.connected_controllers:
            if not self.can_connect_from_origin(controller.origin_name):
                Log.warning("Controller rejected from origin {} (already at the limit)".format(controller.origin_name))
                controller.destroy_selectible()
            else:
                self.connected_controllers[controller.origin_name].append(controller)
        else:
            self.connected_controllers[controller.origin_name] = [controller]

    # Disconnects a controller and calls .disconnect() on it
    # controller  The controller to disconnect
    def deregister_controller(self, controller):
        for c in self.connected_controllers[controller.origin_name]:
            if c == controller:
                self.connected_controllers[c.origin_name].remove(c)
                break

    # called to periodically update this manager
    # cur_time_s  current time in seconds
    def update(self, cur_time_s):
        for C in self.connection_managers:
            C.update(cur_time_s)

        for controllers in list(self.connected_controllers.values()):
            for controller in controllers:
                try:
                    keep = controller.update(cur_time_s)
                except:
                    keep = False
                if not keep:
                    controller.destroy_selectible()

    # Called when this manager needs to free all its resources
    def cleanup(self):
        for controllers in list(self.connected_controllers.values()):
            for controller in controllers:
                controller.destroy_selectible()
        for C in self.connection_managers:
            C.cleanup()

    # Called when a controller sends a command
    # controller  Controller that sent the command
    # command     JSON command sent
    def on_command(self, controller, command):
        if len(command) > 0:
            Log.debug("ControllersManager::on_command({}, {})".format(str(controller), command))

        if not controller.authenticated_user or "authentication" in command:
            ControllerAuthentication.authenticate(controller, command.get("authentication", {}))

        if not controller.authenticated_user:
            controller.send_data({"noauth": "noauth"}) # inform the client that he is not authenticated
            Log.warning("Controller {} trying to communicate without authentication".format(str(controller)))
            controller.destroy_selectible()
            return # don't process anything before authentication

        # heartbeat
        if len(command) == 0:
            controller.send_data({}) # reply
            return

        # Thing state change command
        elif "thing" in command:
            thing_id = command["thing"]
            if controller.things_listening != None and thing_id not in controller.things_listening:
                Log.verboze("ControllersManager::on_command({}, {}) BLOCKED (no access)".format(str(self), command))
                return
            thing = self.core.blueprint.get_thing(thing_id)
            thing.set_state(command, token_from=command.get("token", ""))

        # Control command
        elif "code" in command:
            try:
                if command["code"] == CONTROL_CODES.GET_BLUEPRINT:
                    controller.send_data(self.core.blueprint.get_controller_view(), cache=False)
                elif command["code"] == CONTROL_CODES.GET_THING_STATE:
                    controller.invalidate_cache(thing_id=command.get("thing-id", None))
                elif command["code"] == CONTROL_CODES.SET_LISTENERS:
                    listeners = command.get("things", None)
                    if listeners and type(listeners) is list and reduce(lambda l1, l2: l1 and l2, map(lambda s: type(s) is str, listeners)):
                        controller.things_listening = listeners
                elif command["code"] == CONTROL_CODES.RESET_QRCODE:
                    pass
                elif command["code"] == CONTROL_CODES.SET_QRCODE:
                    pass
            except:
                Log.error("Failed to respond to a control command", exception=True)
                pass
