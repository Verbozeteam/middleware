# enable the simulation Arduino mode
from config.general_config import GENERAL_CONFIG
from config.hardware_config import HARDWARE_CONFIG
GENERAL_CONFIG.SIMULATE_ARDUINO = True

from middleware import Core

import time
import grpc
import testing_utils

class TestHardwareManager(object):
    def setup(self):
        #
        # Setup the Arduino emulator
        #
        channel = grpc.insecure_channel('0.0.0.0:5001')
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.ResetPins(testing_utils.Empty())

        #
        # Setup the system
        #
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/test1.json"
        HARDWARE_CONFIG.LEGACY_MODE = False
        self.core = Core()

    def sync_controller(self):
        self.core.hw_manager.update(1)
        connected_controllers = list(self.core.hw_manager.controller_types["arduino"][1].values())
        assert len(connected_controllers) == 1
        fake_time = 2
        while not connected_controllers[0].is_in_sync():
            self.core.hw_manager.update(fake_time)
            fake_time += 1
            assert fake_time < 30000 # virtual 30 seconds
        assert connected_controllers[0].is_in_sync()

    def test_arduino_connection(self):
        self.sync_controller()

        self.core.hw_manager.on_command("d37", 1)
        time.sleep(0.1)
        assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=37)).state == 1)
        self.core.hw_manager.on_command("d37", 0)
        time.sleep(0.1)
        assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=37)).state == 0)
