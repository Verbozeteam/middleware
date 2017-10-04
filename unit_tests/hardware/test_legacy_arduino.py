# enable the simulation Arduino mode
from unit_tests.hardware.arduino_emulator_tests import BaseLegacyArduinoEmulatorTestUtil

from config.hardware_config import HARDWARE_CONFIG

from middleware import Core
from things.thing import Thing

import time
import testing_utils

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
            self.core.hw_manager.on_command("d"+str(p), 1)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 1

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 0)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 0

        self.is_board_synced()

    def test_arduino_dimmers(self):
        self.sync_board()

        digital_ports = [4, 5, 6, 7]

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 50 + p * 3)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert abs(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state - (50 + (p * 3))) <= 4

        for p in digital_ports:
            self.core.hw_manager.on_command("d"+str(p), 0)
        time.sleep(self.SOCKET_LAG)
        for p in digital_ports:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state == 0

        self.is_board_synced()

    def test_arduino_curtains(self):
        self.sync_board()

        digital_ports = [22, 23, 24, 25, 26, 27]

        # all curtains up
        for p in range(0, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 1)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == list(map(lambda i: 1 - i % 2, range(len(digital_ports))))

        # all curtains down
        for p in range(1, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 1)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == list(map(lambda i: i % 2, range(len(digital_ports))))

        # all curtains stop
        for p in range(0, len(digital_ports), 2):
            self.core.hw_manager.on_command("d"+str(digital_ports[p]), 0)
        time.sleep(self.SOCKET_LAG)
        states = list(map(lambda p: self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=p)).state, digital_ports))
        assert states == [0]*(len(states))

        self.is_board_synced()

    def test_arduino_ac(self):
        self.sync_board()

        # current temperature is 30
        self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=25.0))

        # set the ac set point to 20
        self.core.hw_manager.on_command("v0", 20.0)

        # now we should observe the AC booming:
        # split AC: compressor (port 50 digital) ON
        # central AC: valve open (port 8 PWM)
        time.sleep(0.25) # wait for temperature to be read

        prev_reading = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=8)).state
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=50)).state == 1
        for i in range(0, 8):
            time.sleep(0.25)
            reading = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=8)).state
            compressor = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=50)).state
            if i < 5:
                assert reading <= prev_reading
                assert compressor == 1
                prev_reading = reading
            elif i == 7:
                assert reading == 0
                assert compressor == 0
            self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=25.0-i-1))

        self.is_board_synced()
