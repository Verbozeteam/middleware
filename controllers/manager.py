from logs import Log
from controllers.socket_controller_manager import SocketConnectionManager

class CONTROL_CODES:
    GET_BLUEPRINT = 0

#
# Controllers manager is responsible for all interaction with controller
# devices (tablets, phones, etc...)
#
class ControllersManager(object):
    def __init__(self, core):
        self.core = core
        self.connection_managers = [
            SocketConnectionManager(self)
        ]

    # called to periodically update this manager
    # cur_time_s  current time in seconds
    def update(self, cur_time_s):
        for C in self.connection_managers:
            C.update(cur_time_s)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        for C in self.connection_managers:
            C.cleanup()

    # Called when a Thing wants to broadcast its state to controllers
    # thing_id  id of the Thing that wants to broadcast state
    # state     JSON-serializable dictionary that is the state of the Thing
    def broadcast_thing_state(self, thing_id, state):
        #@TODO: Implement access rights and controllers registering for things updates
        for C in self.connection_managers:
            C.broadcast_thing_state(thing_id, state)

    # Called when a controller sends commands to a particular Thing
    # thing_id  Thing the commands are being sent to
    # commands  List of commands for the Thing
    def send_thing_commands(self, thing_id, commands):
        #@TODO: Implement access rights
        self.core.blueprint.on_controller_data(thing_id, commands)

    # Called when a controller sends a control command
    # command  The control command
    def send_control_command(self, controller, command):
        Log.hammoud("ControllersManager::send_control_command({}, {})".format(str(controller), command))
        try:
            if command["code"] == CONTROL_CODES.GET_BLUEPRINT:
                controller.on_send_data(self.core.blueprint.get_controller_view())
        except:
            pass
