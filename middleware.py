from hardware import HardwareManager
from controllers import ControllersManager
from things import Blueprint
from logs import Log
import time
import argparse

class Core(object):
    def __init__(self):
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Middleware core')
        parser.add_argument("-b", "--blueprint", required=False, type=str, help="Building configuration file", default="blueprint.json")
        self.cmd_args = parser.parse_args()

        Log.info("Initializing the core...")

        # Load blueprint of the building
        self.blueprint = Blueprint(self.cmd_args.blueprint)

        # Initialize hardware manager (Arduino's and such...)
        self.hw_manager = HardwareManager(self)

        # Initialize the controllers manager (tablets, phones, etc...)
        self.ctrl_manager = ControllersManager(self)

    # Main loop for the core (blocks execution)
    def run(self):
        Log.info("Running the core...")
        while True:
            cur_time_s = time.time()
            self.hw_manager.update(cur_time_s)
            self.blueprint.update(cur_time_s)
            self.ctrl_manager.update(cur_time_s)

    # Called when the hardware has an updated value on a port
    # port   Port on which the update happened
    # value  The new value on that port
    def on_hardware_data(self, port, value):
        # forward the update to the blueprint (to dispatch it to the interested Things)
        self.blueprint.on_hardware_data(port, value)

    # Called when the controllers send a command for a Thing
    # thing_id  id of the Thing that the controller is trying to talk to
    # data      data that the controller is sending to the Thing
    def on_controller_data(self, thing_id, data):
        # forward the update to the blueprint (to dispatch it to the interested Things)
        self.blueprint.on_controller_data(thing_id, data)

    # Called by the blueprint when a Thing wants to broadcast its state to controllers
    # thing_id  id of the Thing that wants to broadcast state
    # state     JSON-serializable dictionary that is the state of the Thing
    def broadcast_thing_state(self, thing_id, state):
        # forward the broadcast request to the controllers manager
        self.ctrl_manager.broadcast_thing_state(thing_id, state)

if __name__ == '__main__':
    # Initialize logging
    Log.initialize()

    # Initialize and run the core
    core = Core()
    core.run()
