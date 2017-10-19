
from hardware import HardwareManager
from controllers import ControllersManager
from things import Blueprint
from logs import Log
import time

from core.select_service import SelectService

class Core(object):
    def __init__(self):
        Log.info("Initializing the core...")

        # Load blueprint of the building
        self.blueprint = Blueprint(self)

        # Initialize hardware manager (Arduino's and such...)
        self.hw_manager = HardwareManager(self)

        # Initialize the controllers manager (tablets, phones, etc...)
        self.ctrl_manager = ControllersManager(self)

    def update(self, cur_time_s):
        #self.hw_manager.update(cur_time_s)
        self.ctrl_manager.update(cur_time_s)

        SelectService.perform_select(cur_time_s, select_writes=False)

        for thing in self.blueprint.get_things():
            try:
                thing.update(cur_time_s)
            except:
                Log.error("Thing {} failed to update".format(thing.id), exception=True)

        SelectService.perform_select(cur_time_s, select_reads=False)

    # Main loop for the core (blocks execution)
    def run(self):
        Log.info("Running the core...")
        while True:
            cur_time_s = time.time()
            self.update(cur_time_s)

    def cleanup(self):
        self.hw_manager.cleanup()
        self.blueprint.cleanup()
        self.ctrl_manager.cleanup()
