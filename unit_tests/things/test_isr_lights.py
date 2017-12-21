from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.full_system import FullSystem
from config.general_config import GENERAL_CONFIG

from things.light import Dimmer

import time
import testing_utils

class TestISRDimmers(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/isr_lights.json"
        super(TestISRDimmers, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.switches = list(filter(lambda t: type(t) is Dimmer, self.things))

    def teardown(self):
        self.system.destroy()
        super(TestISRDimmers, self).teardown()

    def test_controller_input(self):
        self.system.arduino_emulator.sync_board()

        assert len(self.switches) > 0

        for s in self.switches:
            s.set_state({"intensity": 100})
        self.wait_for_condition(lambda self: self.system.arduino_emulator.get_isr_state() == (100, 10, s.virtual_port_data[0][2])) # (full_period, wavelength, sync)

        for s in self.switches:
            self.wait_for_condition(lambda self:
                self.system.arduino_emulator.get_isr_pin(index=s.virtual_port_data[0][-1]) >= s.get_hardware_state()[s.dimmer_port] and
                s.get_state()["intensity"] == 100
            )

        assert self.system.arduino_emulator.is_board_synced()

        for s in self.switches:
            s.set_state({"intensity": 0})
        self.wait_for_condition(lambda self: self.system.arduino_emulator.get_isr_state() == (100, 10, s.virtual_port_data[0][2])) # (full_period, wavelength, sync)

        for s in self.switches:
            self.wait_for_condition(lambda self:
                self.system.arduino_emulator.get_isr_pin(index=s.virtual_port_data[0][-1]) >= s.get_hardware_state()[s.dimmer_port] and
                s.get_state()["intensity"] == 0
            )

        assert self.system.arduino_emulator.is_board_synced()
