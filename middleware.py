from hardware import HardwareManager
from controllers import ControllersManager
from things import Blueprint
from logs import Log
import time

import config.cmd_args

class Core(object):
    def __init__(self):
        Log.info("Initializing the core...")

        # Load blueprint of the building
        self.blueprint = Blueprint(self)

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

    def cleanup(self):
        self.hw_manager.cleanup()
        self.blueprint.cleanup()
        self.ctrl_manager.cleanup()

if __name__ == '__main__':
    # Initialize and run the core
    core = Core()
    core.run()
    core.cleanup()
