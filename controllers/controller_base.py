from core.select_service import Selectible
from logs import Log

class Controller(Selectible):
    def __init__(self, controllers_manager):
        self.manager = controllers_manager
        self.manager.register_controller(self)
        Log.info("Controller connected: {}".format(str(controller)))

    def destroy_selectible(self):
        self.manager.deregister_controller(self)
        Log.info("Controller disconnected: {}".format(str(controller)))

    # Called for a periodic update
    def update(self, cur_time_s):
        pass

    # Called when the controller has pending bytes to read
    def on_read_data(self):
        pass

    # Called when data needs to be sent to the remote controller
    def on_send_data(self, json_data):
        pass
