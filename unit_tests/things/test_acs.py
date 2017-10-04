from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil, BaseLegacyArduinoEmulatorTestUtil

from config.general_config import GENERAL_CONFIG

from things.air_conditioner import SplitAC, CentralAC

import time
import testing_utils

class BaseCentralACTester(BaseArduinoEmulatorTestUtil):
    def test_controller_input_fan(self):
        self.sync_board()

        # fan on
        self.ac.on_controller_data({"fan": 1})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.ac.fan_port[1:]))).state == 1
        assert self.ac.get_state()["fan"] == 1

        # fan off
        self.ac.on_controller_data({"fan": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.ac.fan_port[1:]))).state == 0
        assert self.ac.get_state()["fan"] == 0

        self.is_board_synced()

    def test_controller_input_set_point(self):
        self.sync_board()
        self.ac.on_controller_data({"set_pt": 26})
        assert self.ac.get_state()["set_pt"] == 26
        self.is_board_synced()

    def test_board_input(self):
        self.ac.input_ports[self.ac.temperature_port] = 100 # make the temperature reports rapid so the test finishes quicker...
        self.sync_board()

        for T in range(12, 20, 2):
            self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=T))
            time.sleep(self.SOCKET_LAG)

            for i in range(0, 10):
                self.core.hw_manager.update(T*30 + i*2 + 2)
                if abs(self.ac.get_state()["temp"] - T) < 0.1:
                    break
                time.sleep(0.1)

            assert abs(self.ac.get_state()["temp"] - T) < 0.1

            self.is_board_synced()

    def test_operation_logic(self):
        # set the sensor temperature to follow the valve, and see if we reach the set point

        self.ac.input_ports[self.ac.temperature_port] = 10 # make the temperature reports rapid so the test finishes quicker...
        self.sync_board()

        set_points = [16.0, 32.0, 25.0]

        cur_sensor_temp = 25.0
        self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=cur_sensor_temp))

        cur_time = 1
        for SP in set_points:
            self.ac.on_controller_data({"set_pt": SP})

            for i in range(0, 600):
                self.core.hw_manager.update(cur_time)
                self.core.blueprint.update(cur_time)
                cur_time += 2
                valve_value = self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.ac.valve_port[1:]))).state
                valve_effectiveness = 32 - (valve_value * (32.0/255.0)) # [0, 32]
                cur_sensor_temp += (valve_effectiveness-cur_sensor_temp) * 0.1
                self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=cur_sensor_temp))

            assert abs(cur_sensor_temp - SP) < 1.0

        self.is_board_synced()


class TestCentralAC(BaseCentralACTester, BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/central_ac.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.ac = list(filter(lambda t: type(t) is CentralAC, self.things))[0]

# Too much of a hassle, and waste of time to test...
# class TestLegacyCentralAC(BaseCentralACTester, BaseLegacyArduinoEmulatorTestUtil):
#     def setup(self):
#         GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/central_ac.json"
#         BaseLegacyArduinoEmulatorTestUtil.setup(self)

#         self.things = self.core.blueprint.get_things()
#         self.ac = list(filter(lambda t: type(t) is CentralAC, self.things))[0]

