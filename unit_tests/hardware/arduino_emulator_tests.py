# enable the simulation Arduino mode
from config.hardware_config import HARDWARE_CONFIG

from middleware import Core

import grpc
import testing_utils

class BaseArduinoEmulatorTestUtil(object):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5001"
    SOCKET_LAG = 0.05 # assume 50ms lag until things reach arduino

    def setup(self):
        #
        # Setup the Arduino emulator
        #
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.ResetPins(testing_utils.Empty())

        #
        # Setup the system
        #
        HARDWARE_CONFIG.LEGACY_MODE = False # make sure we are not in legacy mode
        self.core = Core()

    def sync_board(self):
        self.core.hw_manager.update(1)
        self.connected_boards = list(self.core.hw_manager.controller_types["arduino"][1].values())
        assert len(self.connected_boards) == 1
        fake_time = 2
        while not self.connected_boards[0].is_in_sync():
            self.core.hw_manager.update(fake_time)
            fake_time += 1
            assert fake_time < 30000 # virtual 30 seconds
        self.is_board_synced()

    def is_board_synced(self):
        assert len(self.connected_boards) == 1
        assert self.connected_boards[0].is_in_sync()

class BaseLegacyArduinoEmulatorTestUtil(object):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5002"
    SOCKET_LAG = 0.05 # assume 50ms lag until things reach arduino

    def setup(self):
        #
        # Setup the Arduino emulator
        #
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=44, state=1)) # make sure hotel card is in (pin 44)

        #
        # Setup the system
        #
        HARDWARE_CONFIG.LEGACY_MODE = True # make sure we are in legacy mode
        self.core = Core()

    def sync_board(self):
        self.core.hw_manager.update(1)
        self.connected_controllers = list(self.core.hw_manager.controller_types["arduino"][1].values())
        self.is_board_synced()

    def is_board_synced(self):
        assert len(self.connected_controllers) == 1