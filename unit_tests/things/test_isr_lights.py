from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil

from config.general_config import GENERAL_CONFIG

from things.light import Dimmer

import time
import testing_utils

class TestISRSwitches(BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/isr_lights.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.switches = list(filter(lambda t: type(t) is Dimmer, self.things))

    def test_controller_input(self):
        self.sync_board()

        assert len(self.switches) > 0

        for s in self.switches:
            s.on_controller_data({"intensity": 100})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)

        state = self.arduino_emu.GetISRState(testing_utils.Empty())
        assert state.full_period == 100
        assert state.wavelength == 10
        assert state.sync == s.virtual_port_data[0][2]

        for s in self.switches:
            assert self.arduino_emu.GetISRPinState(testing_utils.ISRPin(index=s.virtual_port_data[0][-1])).state == s.virtual_port_data[0][1]-1
            assert s.get_state()["intensity"] == 100

        self.is_board_synced()

        for s in self.switches:
            s.on_controller_data({"intensity": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)

        state = self.arduino_emu.GetISRState(testing_utils.Empty())
        assert state.full_period == 100
        assert state.wavelength == 10
        assert state.sync == s.virtual_port_data[0][2]

        for s in self.switches:
            assert self.arduino_emu.GetISRPinState(testing_utils.ISRPin(index=s.virtual_port_data[0][-1])).state == 0
            assert s.get_state()["intensity"] == 0

        self.is_board_synced()
