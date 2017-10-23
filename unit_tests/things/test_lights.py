from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.full_system import FullSystem
from config.general_config import GENERAL_CONFIG

from things.light import LightSwitch, Dimmer

import time
import testing_utils
import random

#
# SWITCHES
#

class TestSwitches(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        super(TestSwitches, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.switches = list(filter(lambda t: type(t) is LightSwitch, self.things))

    def teardown(self):
        self.system.destroy()
        super(TestSwitches, self).teardown()

    def test_controller_input(self):
        assert len(self.switches) > 0

        self.system.arduino_emulator.sync_board()

        for i in reversed(range(0, 2)):
            for s in random.sample(self.switches, 4):
                s.set_state({"intensity": i})
                assert s.get_state()["intensity"] == i
                assert s.get_hardware_state()[s.switch_port] == i

                def controller_received_update(self):
                    self.system.fake_controllers[0].recv_json(10000, timeout=0.1)
                    return self.system.fake_controllers[0].cache.get(s.id, {}) == s.get_state()
                self.wait_for_condition(controller_received_update)

                self.wait_for_condition(lambda self: self.system.arduino_emulator.get_pin(type=0, index=int(s.switch_port[1:])) == i)

    def test_wakeup_and_sleep(self):
        # test without a default wakeup value
        for s in self.switches:
            if hasattr(s, "default_wakeup_value"):
                delattr(s, "default_wakeup_value")

            s.intensity = 1
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 1

            s.intensity = 0
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 0

        # test with default wakeup value
        for s in self.switches:
            s.default_wakeup_value = 1

            s.intensity = 0
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 1

#
# DIMMERS
#

class TestDimmers(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"

        super(TestDimmers, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.dimmers = list(filter(lambda t: type(t) is Dimmer, self.things))

    def teardown(self):
        self.system.destroy()
        super(TestDimmers, self).teardown()

    def test_controller_input(self):
        assert len(self.dimmers) > 0

        self.system.arduino_emulator.sync_board()

        for val in range(0, 101, 50):
            for s in self.dimmers:
                s.set_state({"intensity": val})
                assert s.get_state()["intensity"] == val
                assert abs(s.get_hardware_state()[s.dimmer_port] - int(val*2.55)) <= 1.0

                def controller_received_update(self):
                    self.system.fake_controllers[0].recv_json(10000, timeout=0)
                    return self.system.fake_controllers[0].cache.get(s.id, {}) == s.get_state()
                self.wait_for_condition(controller_received_update)

                self.wait_for_condition(lambda self: abs(self.system.arduino_emulator.get_pin(type=0, index=int(s.dimmer_port[1:])) - int(val*2.55)) <= 1.0)

    def test_wakeup_and_sleep(self):
        # test without a default wakeup value
        for s in self.dimmers:
            if hasattr(s, "default_wakeup_value"):
                delattr(s, "default_wakeup_value")

            s.intensity = 100
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 100

            s.intensity = 0
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 0

        # test with default wakeup value
        for s in self.dimmers:
            s.default_wakeup_value = 20

            s.intensity = 0
            s.sleep()
            assert s.intensity == 0

            s.wake_up()
            assert s.intensity == 20

