# enable the simulation Arduino mode
from config.general_config import GENERAL_CONFIG
from config.hardware_config import HARDWARE_CONFIG
GENERAL_CONFIG.SIMULATE_ARDUINO = True

from middleware import Core
from things.thing import Thing

import time
import grpc
import testing_utils

class BaseArduinoTestUtil(object):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5002"
    SOCKET_LAG = 0.05 # assume 50ms lag until things reach arduino

    def setup(self):
        #
        # Setup the Arduino emulator
        #
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=44, state=1)) # make sure hotel card is in

        #
        # Setup the system
        #
        HARDWARE_CONFIG.LEGACY_MODE = True # make sure we are in legacy mode
        self.core = Core()

    def sync_controller(self):
        self.core.hw_manager.update(1)
        self.connected_controllers = list(self.core.hw_manager.controller_types["arduino"][1].values())
        self.is_controller_synced()

    def is_controller_synced(self):
        assert len(self.connected_controllers) == 1

class TestLegacyArduinoController(BaseArduinoTestUtil):

    # curtains   : 22+ (UP, DOWN, UP, DOWN, ...)
    # onoff      : 37-
    # fans       : 48-49
    # ACs        : 50-51
    # temp sensor: 53
    # dimmers    : 4-7 (analog PWM output)
    # central ACs: 8-9 (analog PWM output)
    # SYNC       : digital 3
    # hotel card : 44 (input 0v/5v)
    # hotel power: 42 (output 0v/5v)

    def test_arduino_connection(self):
        self.sync_controller()
        self.is_controller_synced()

    def test_arduino_switches(self):
        self.sync_controller()

        digital_ports = [30, 31, 32, 33, 34, 35, 36, 37]

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 1)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 1

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 0)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 0

        self.is_controller_synced()

    def test_arduino_dimmers(self):
        self.sync_controller()

        digital_ports = [4, 5, 6, 7]

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), p * 2)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == int((p * 2) * 2.55)

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 0)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 0

        self.is_controller_synced()

    def test_arduino_curtains(self):
        self.sync_controller()

        digital_ports = [22, 23, 24, 25, 26, 27]

        # all curtains up
        for p in range(0, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 1)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == list(map(lambda i: i % 2, range(len(digital_ports))))

        # all curtains down
        for p in range(1, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 1)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == list(map(lambda i: 1 - (i % 2), range(len(digital_ports))))

        # all curtains stop
        for p in range(0, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 0)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == [0]*(len(states))

        self.is_controller_synced()
