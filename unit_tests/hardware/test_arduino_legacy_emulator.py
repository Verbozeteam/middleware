from unit_tests.utilities.base_framework import BaseTestFramework
from config.hardware_config import HARDWARE_CONFIG

import grpc
import testing_utils

class BaseLegacyArduinoEmulatorTestUtil(BaseTestFramework):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5002"

    def setup(self):
        # Setup the Arduino emulator
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=44, state=1)) # make sure hotel card is in (pin 44)

        self.LEGACY_MODE = True # make sure we are in legacy mode
        super(BaseLegacyArduinoEmulatorTestUtil, self).setup()
        self.core.blueprint.rooms = [] # asume no rooms and no things exist...

    def sync_board(self):
        self.core.update(1)
        self.connected_boards = list(self.core.hw_manager.connected_controllers.values())
        assert len(self.connected_boards) == 1

    def is_board_synced(self):
        return len(self.connected_boards) == 1

class TestLegacyArduinoController(BaseLegacyArduinoEmulatorTestUtil):
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
        self.sync_board()

    def test_arduino_switches(self):
        self.sync_board()

        digital_ports = [30, 31, 32, 33, 34, 35, 36, 37]

        for p in digital_ports:
           self.connected_boards[0].set_port_value("d"+str(p), 1)

        def switches_are_set(self):
            for p in digital_ports:
                if self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state != 1:
                    return False
            return True

        self.wait_for_condition(switches_are_set)

        for p in digital_ports:
            self.connected_boards[0].set_port_value("d"+str(p), 0)

        def switches_are_unset(self):
            for p in digital_ports:
                if self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state != 0:
                    return False
            return True

        self.wait_for_condition(switches_are_unset)

        assert self.is_board_synced()

    def test_arduino_dimmers(self):
        self.sync_board()

        digital_ports = [4, 5, 6, 7]

        for p in digital_ports:
           self.connected_boards[0].set_port_value("d"+str(p), 50 + p * 3)

        def dimmers_are_set(self):
            for p in digital_ports:
                if abs(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state - (50 + (p * 3))) > 4:
                    return False
            return True

        self.wait_for_condition(dimmers_are_set)

        for p in digital_ports:
           self.connected_boards[0].set_port_value("d"+str(p), 0)

        def dimmers_are_unset(self):
            for p in digital_ports:
                if abs(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state - 0) > 4:
                    return False
            return True

        self.wait_for_condition(dimmers_are_unset)

        assert self.is_board_synced()

    def test_arduino_curtains(self):
        self.sync_board()

        digital_ports = [22, 23, 24, 25, 26, 27]

        # all curtains up
        for p in range(0, len(digital_ports), 2):
           self.connected_boards[0].set_port_value("d"+str(digital_ports[p]), 1)

        def curtains_are_up(self):
            states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
            return states == list(map(lambda i: 1 - i % 2, range(len(digital_ports))))

        self.wait_for_condition(curtains_are_up)

        # all curtains down
        for p in range(1, len(digital_ports), 2):
           self.connected_boards[0].set_port_value("d"+str(digital_ports[p]), 1)

        def curtains_are_down(self):
            states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
            return states == list(map(lambda i: i % 2, range(len(digital_ports))))

        self.wait_for_condition(curtains_are_down)

        # all curtains stop
        for p in range(1, len(digital_ports), 2):
           self.connected_boards[0].set_port_value("d"+str(digital_ports[p]), 0)

        def curtains_are_off(self):
            states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
            return states == [0]*(len(states))

        self.wait_for_condition(curtains_are_off)

        assert self.is_board_synced()

    # Fuck this test.
    # def test_arduino_ac(self):
    #     self.sync_board()

    #     # current temperature is 26
    #     self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=26.0))

    #     # set the ac set point to 20
    #     self.core.hw_manager.on_command("v0", 20.0)

    #     # now we should observe the AC booming:
    #     # split AC: compressor (port 50 digital) ON
    #     # central AC: valve open (port 8 PWM)

    #     prev_reading = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=8)).state
    #     assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=50)).state == 1
    #     for i in range(0, 8):
    #         time.sleep(0.25)
    #         reading = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=8)).state
    #         compressor = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=50)).state
    #         if i < 5:
    #             assert reading <= prev_reading
    #             assert compressor == 1
    #             prev_reading = reading
    #         elif i == 7:
    #             assert reading == 0
    #             assert compressor == 0
    #         self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=25.0-i-1))

    #     assert self.is_board_synced()
