from logs import Log
from controllers.socket_controller import SocketController

#
# Controllers manager is responsible for all interaction with controller
# devices (tablets, phones, etc...)
#
class ControllersManager(object):
    def __init__(self, core):
        self.core = core

    # called to periodically update this manager
    # cur_time_s  current time in seconds
    def update(self, cur_time_s):
        pass

    # Called when a Thing wants to broadcast its state to controllers
    # thing_id  id of the Thing that wants to broadcast state
    # state     JSON-serializable dictionary that is the state of the Thing
    def broadcast_thing_state(self, thing_id, state):
        pass



