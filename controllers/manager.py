from logs import Log
from controllers.tcp_socket_controllers import TCPSocketConnectionManager

class CONTROL_CODES:
    GET_BLUEPRINT = 0
    GET_THING_STATE = 1

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

        for controller in self.connected_controllers:
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

    # # Called when a Thing wants to broadcast its state to controllers
    # # thing_id  id of the Thing that wants to broadcast state
    # # state     JSON-serializable dictionary that is the state of the Thing
    # def broadcast_thing_state(self, thing_id, state):
    #     #@TODO: Implement access rights and controllers registering for things updates
    #     for C in self.connection_managers:
    #         C.broadcast_thing_state(thing_id, state)

    # # Called when a controller sends commands to a particular Thing
    # # thing_id  Thing the commands are being sent to
    # # commands  List of commands for the Thing
    # def send_thing_commands(self, thing_id, commands):
    #     #@TODO: Implement access rights
    #     self.core.blueprint.on_controller_data(thing_id, commands)

    # # Called when a controller sends a control command
    # # command  The control command (JSON)
    # def send_control_command(self, controller, command):
    #     Log.hammoud("ControllersManager::send_control_command({}, {})".format(str(controller), command))
    #     try:
    #         if command["code"] == CONTROL_CODES.GET_BLUEPRINT:
    #             controller.on_send_data(self.core.blueprint.get_controller_view())
    #         elif command["code"] == CONTROL_CODES.GET_THING_STATE:
    #             all_things = self.core.blueprint.get_things()
    #             if "thing-id" in command:
    #                 all_things = list(filter(lambda t: t.id == command["thing-id"], all_things))
    #             for T in all_things:
    #                 controller.on_thing_state(T.id, T.get_state())
    #     except Exception as e:
    #         pass
