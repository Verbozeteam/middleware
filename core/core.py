from config.general_config import GENERAL_CONFIG
from hardware import HardwareManager
from controllers import ControllersManager
from things import Blueprint
from logs import Log
import time

from core.select_service import SelectService

class Core(object):
    cur_time_s = 0

    def __init__(self):
        Log.info("Initializing the core...")

        # Load blueprint of the building
        self.blueprint = Blueprint(self)

        # Initialize hardware manager (Arduino's and such...)
        self.hw_manager = HardwareManager(self)

        # Initialize the controllers manager (tablets, phones, etc...)
        self.ctrl_manager = ControllersManager(self)

    def update(self, cur_time_s):
        self.cur_time_s = cur_time_s

        self.hw_manager.update(cur_time_s)
        self.ctrl_manager.update(cur_time_s)

        SelectService.perform_select(cur_time_s, select_writes=False) # only reads

        self.hw_manager.update(cur_time_s)
        self.ctrl_manager.update(cur_time_s)

        SelectService.select_timeout = GENERAL_CONFIG.SELECT_TIMEOUT

        need_reupdate = False
        for thing in self.blueprint.get_things():
            try:
                need_reupdate = need_reupdate or thing.update(cur_time_s)
            except:
                Log.error("Thing {} failed to update".format(thing.id), exception=True)

        if need_reupdate:
            SelectService.select_timeout = 0 # this will make the select not wait so that Thing updates happen again shortly

        self.hw_manager.update(cur_time_s)
        self.ctrl_manager.update(cur_time_s)

        SelectService.perform_select(cur_time_s, select_reads=False) # only writes

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
