from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil, BaseLegacyArduinoEmulatorTestUtil

from config.general_config import GENERAL_CONFIG

from things.light import LightSwitch, Dimmer

import time
import testing_utils

#
# SWITCHES
#

class BaseSwitchTester(object):
    def test_controller_input(self):
        self.sync_board()

        assert len(self.switches) > 0

        # turn all on
        for s in self.switches:
            s.on_controller_data({"intensity": 1})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for s in self.switches:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(s.switch_port[1:]))).state == 1
            assert s.get_state()["intensity"] == 1

        self.is_board_synced()

        # turn all off
        for s in self.switches:
            s.on_controller_data({"intensity": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for s in self.switches:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(s.switch_port[1:]))).state == 0
            assert s.get_state()["intensity"] == 0

        self.is_board_synced()

    def test_rebroadcasting(self):
        self.sync_board()

        for s in self.switches:
            s.on_controller_data({"intensity": 1})

        broadcasts = {}
        def broadcast_thing_state(thing):
            broadcasts[thing.id] = thing
            assert thing.get_state()["intensity"] == 1

        self.core.blueprint.broadcast_thing_state = broadcast_thing_state
        self.core.blueprint.update(1)
        assert len(broadcasts.keys()) == len(self.switches)

        self.is_board_synced()

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


class TestSwitches(BaseSwitchTester, BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.switches = list(filter(lambda t: type(t) is LightSwitch, self.things))

class TestSwitchesLegacy(BaseSwitchTester, BaseLegacyArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        BaseLegacyArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.switches = list(filter(lambda t: type(t) is LightSwitch, self.things))


#
# DIMMERS
#

class BaseDimmerTester(object):
    def test_controller_input(self):
        self.sync_board()

        assert len(self.dimmers) > 0

        # set all to positive dimming
        for s in range(0, len(self.dimmers)):
            self.dimmers[s].on_controller_data({"intensity": 20 + s*2})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for s in range(0, len(self.dimmers)):
            assert abs(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.dimmers[s].pwm_port[1:]))).state - ((20 + s*2) * 2.55)) <= 4.0
            assert self.dimmers[s].get_state()["intensity"] == 20 + s*2

        self.is_board_synced()

        # set all to 0
        for s in self.dimmers:
            s.on_controller_data({"intensity": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for s in self.dimmers:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(s.pwm_port[1:]))).state == 0
            assert s.get_state()["intensity"] == 0

        self.is_board_synced()

    def test_rebroadcasting(self):
        self.sync_board()

        for s in self.dimmers:
            s.on_controller_data({"intensity": 100})

        broadcasts = {}
        def broadcast_thing_state(thing):
            broadcasts[thing.id] = thing
            assert thing.get_state()["intensity"] == 100

        self.core.blueprint.broadcast_thing_state = broadcast_thing_state
        self.core.blueprint.update(1)
        assert len(broadcasts.keys()) == len(self.dimmers)

        self.is_board_synced()

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

class TestDimmers(BaseDimmerTester, BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.dimmers = list(filter(lambda t: type(t) is Dimmer, self.things))

class TestDimmersLegacy(BaseDimmerTester, BaseLegacyArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        BaseLegacyArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.dimmers = list(filter(lambda t: type(t) is Dimmer, self.things))

