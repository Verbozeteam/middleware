from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil, BaseLegacyArduinoEmulatorTestUtil

from config.general_config import GENERAL_CONFIG

from things.curtain import Curtain

import time
import testing_utils

class BaseCurtainsTester(object):
    def test_controller_input(self):
        self.sync_board()

        assert len(self.curtains) > 0

        # move up
        for c in self.curtains:
            c.on_controller_data({"curtain": 1})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for c in self.curtains:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.up_port[1:]))).state == 1
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.down_port[1:]))).state == 0

        self.is_board_synced()

        # move down
        for c in self.curtains:
            c.on_controller_data({"curtain": 2})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for c in self.curtains:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.up_port[1:]))).state == 0
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.down_port[1:]))).state == 1

        self.is_board_synced()

        # stop
        for c in self.curtains:
            c.on_controller_data({"curtain": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        for c in self.curtains:
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.up_port[1:]))).state == 0
            assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(c.down_port[1:]))).state == 0

        self.is_board_synced()

class TestCurtains(BaseCurtainsTester, BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/curtains.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.curtains = list(filter(lambda t: type(t) is Curtain, self.things))

class TestCurtainsLegacy(BaseCurtainsTester, BaseLegacyArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/curtains.json"
        BaseLegacyArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.curtains = list(filter(lambda t: type(t) is Curtain, self.things))
