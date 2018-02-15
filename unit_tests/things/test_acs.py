from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.full_system import FullSystem
from config.general_config import GENERAL_CONFIG

from things.air_conditioner import SplitAC, CentralAC

import time
import testing_utils
import math

class TestCentralAC(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/central_ac.json"
        super(TestCentralAC, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.ac = list(filter(lambda t: type(t) is CentralAC, self.things))[0]

    def teardown(self):
        self.system.destroy()
        super(TestCentralAC, self).teardown()

    def test_controller_input_fan(self):
        self.system.arduino_emulator.sync_board()

        # fan HIGH
        self.ac.set_state({"fan": 3})
        self.wait_for_condition(lambda self:
            self.ac.get_state()["fan"] == 3 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_low_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_medium_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_high_port[1:])) == 1
        )

        # fan MEDIUM
        self.ac.set_state({"fan": 2})
        self.wait_for_condition(lambda self:
            self.ac.get_state()["fan"] == 2 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_low_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_medium_port[1:])) == 1 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_high_port[1:])) == 0
        )

        # fan LOW
        self.ac.set_state({"fan": 1})
        self.wait_for_condition(lambda self:
            self.ac.get_state()["fan"] == 1 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_low_port[1:])) == 1 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_medium_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_high_port[1:])) == 0
        )

        # fan off
        self.ac.set_state({"fan": 0})
        self.wait_for_condition(lambda self:
            self.ac.get_state()["fan"] == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_low_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_medium_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.fan_high_port[1:])) == 0
        )

        assert self.system.arduino_emulator.is_board_synced()

    def test_controller_input_set_point(self):
        self.system.arduino_emulator.sync_board()
        self.ac.set_state({"set_pt": 26})
        assert self.ac.get_state()["set_pt"] == 26
        assert self.system.arduino_emulator.is_board_synced()

    def test_board_input(self):
        self.ac.input_ports[self.ac.temperature_port] = 100 # make the temperature reports rapid so the test finishes quicker...
        self.system.arduino_emulator.sync_board()

        for T in range(12, 20, 2):
            self.system.arduino_emulator.set_temp(temp=T)
            self.wait_for_condition(lambda self: abs(self.ac.get_state()["temp"] - T) < 0.1)
            assert self.system.arduino_emulator.is_board_synced()

    def test_pwm_valve_operation_logic(self):
        self.ac.input_ports[self.ac.temperature_port] = 10 # make the temperature reports rapid so the test finishes quicker...
        self.system.arduino_emulator.sync_board()

        set_points = [16.0, 32.0, 25.0, 8.0]

        cur_sensor_temp = 25.0
        self.system.arduino_emulator.set_temp(temp=cur_sensor_temp)

        for SP in set_points:
            # set the set point, then set the temperature, then wait for the valve to chane in the right direction
            self.ac.set_state({"set_pt": SP})
            self.system.arduino_emulator.set_temp(temp=20.0)
            self.wait_for_condition(lambda self: abs(self.ac.get_state()["temp"] - 20.0) <= 0.1)
            starting_valve_value = self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.valve_port[1:]))
            expected_change = min(max((20.0 - SP)*10000, -1.5), 1.5)
            def monitor(self):
                self.ac.next_valve_update = 0
                cur_valve = self.system.arduino_emulator.get_pin(type=0, index=int(self.ac.valve_port[1:]))
                return (cur_valve - starting_valve_value) >= expected_change
            self.wait_for_condition(monitor)

        assert self.system.arduino_emulator.is_board_synced()

    def test_digital_valve_operation_logic(self):
        self.ac.input_ports[self.ac.temperature_port] = 10 # make the temperature reports rapid so the test finishes quicker...
        self.system.arduino_emulator.sync_board()

        #
        # Set the set point to 25.0
        # Set the temperatures and observe...
        # 30.0             => valve open
        # 26.0             => valve open
        # 25.0             => valve open
        # 25.0-homeostasis => valve closed
        # 23.0             => valve closed
        # 25.0             => valve closed
        # 25.0+homeostasis => valve open
        #

        self.ac.set_state({"set_pt": 25.0})
        steps = [(30.0, 1), (26.0, 1), (25.0, 1), (math.floor(25.0-self.ac.homeostasis), 0), (23.0, 0), (25.0, 0), (math.ceil(25.0+self.ac.homeostasis), 1)]
        for (cur_temp, expected_valve_state) in steps:
            self.system.arduino_emulator.set_temp(temp=cur_temp)
            self.wait_for_condition(lambda self: self.ac.get_hardware_state()[self.ac.digital_valve_port] == expected_valve_state)

        assert self.system.arduino_emulator.is_board_synced()

    def test_wakeup_and_sleep(self):
        # test without default wakeup/sleep values
        if hasattr(self.ac, "default_wakeup_temperature"):
            delattr(self.ac, "default_wakeup_temperature")
        if hasattr(self.ac, "default_sleep_temperature"):
            delattr(self.ac, "default_sleep_temperature")

        self.ac.current_set_point = 16.0
        self.ac.current_fan_speed = 0
        self.ac.sleep()
        assert self.ac.current_fan_speed == 1 and abs(self.ac.current_set_point - 25.0) < 0.1

        self.ac.wake_up()
        assert self.ac.current_fan_speed == 0 and abs(self.ac.current_set_point - 16.0) < 0.1

        # test with default wakeup/sleep values
        self.ac.default_sleep_temperature = 30.0
        self.ac.default_wakeup_temperature = 20.0

        self.ac.current_set_point = 500.0
        self.ac.current_fan_speed = 0
        self.ac.sleep()
        assert self.ac.current_fan_speed == 1 and abs(self.ac.current_set_point - self.ac.default_sleep_temperature) < 0.1

        self.ac.wake_up()
        assert self.ac.current_fan_speed == 1 and abs(self.ac.current_set_point - self.ac.default_wakeup_temperature) < 0.1
