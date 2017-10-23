from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.full_system import FullSystem
from config.general_config import GENERAL_CONFIG

from things.curtain import Curtain

import time
import testing_utils

class TestCurtains(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/curtains.json"
        super(TestCurtains, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.curtains = list(filter(lambda t: type(t) is Curtain, self.things))

    def teardown(self):
        self.system.destroy()
        super(TestCurtains, self).teardown()

    def test_controller_input(self):
        self.system.arduino_emulator.sync_board()

        assert len(self.curtains) > 0

        # move up
        for c in self.curtains:
            c.set_state({"curtain": 1})
        self.wait_for_condition(lambda self:
            self.system.arduino_emulator.get_pin(type=0, index=int(c.up_port[1:])) == 1 and
            self.system.arduino_emulator.get_pin(type=0, index=int(c.down_port[1:])) == 0
        )

        assert self.system.arduino_emulator.is_board_synced()

        # move down
        for c in self.curtains:
            c.set_state({"curtain": 2})
        self.wait_for_condition(lambda self:
            self.system.arduino_emulator.get_pin(type=0, index=int(c.up_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(c.down_port[1:])) == 1
        )

        assert self.system.arduino_emulator.is_board_synced()

        # stop
        for c in self.curtains:
            c.set_state({"curtain": 0})
        self.wait_for_condition(lambda self:
            self.system.arduino_emulator.get_pin(type=0, index=int(c.up_port[1:])) == 0 and
            self.system.arduino_emulator.get_pin(type=0, index=int(c.down_port[1:])) == 0
        )

        assert self.system.arduino_emulator.is_board_synced()
