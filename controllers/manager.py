from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG
from controllers.tcp_socket_controllers import TCPSocketConnectionManager, TCPSSLSocketConnectionManager
from controllers.authentication import ControllerAuthentication, TOKEN_TYPE

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

    # Gets all connected and authenticated controllers with the given token type
    def get_controllers_by_type(self, token_type):
        ret = []
        for origin in self.connected_controllers:
            for controller in self.connected_controllers[origin]:
                if controller.authenticated_user and controller.authenticated_user.token_type == token_type:
                    ret.append(controller)
        return ret

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
            if thing:
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
                    # find a hub and forward the code to
                    hubs = self.get_controllers_by_type(TOKEN_TYPE.HUB)
                    if len(hubs) > 0:
                        hubs[0].send_data({"code": CONTROL_CODES.RESET_QRCODE})
                    else:
                        Log.warning("Trying to reset QR code but no connected hub was found")
                elif command["code"] == CONTROL_CODES.SET_QRCODE:
                    self.core.blueprint.display["QRCodeAddress"] = command.get("qr-code", "")
                    controllers = self.get_controllers_by_type(TOKEN_TYPE.CONTROLLER)
                    for controller in controllers:
                        controller.send_data(self.core.blueprint.get_controller_view(), cache=False)
            except:
                Log.error("Failed to respond to a control command", exception=True)

        # Hardware changes command
        elif "port" in command and "value" in command:
            try:
                self.core.hw_manager.on_port_update(controller, command["port"], command["value"])
            except:
                Log.error("Failed to respond to a port update command", exception=True)


    # Called when a controller authenticates
    def on_controller_authenticated(self, controller):
        pass
