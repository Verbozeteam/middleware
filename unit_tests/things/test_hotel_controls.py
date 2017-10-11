from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil

from unittest.mock import Mock

from config.general_config import GENERAL_CONFIG

from things.hotel_controls import HotelControls

import time
import testing_utils

class TestHotelControls(BaseArduinoEmulatorTestUtil):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/hotel_controls.json"
        BaseArduinoEmulatorTestUtil.setup(self)

        self.things = self.core.blueprint.get_things()
        self.hotel_controls = self.things[0]

    def set_card(self, state=1):
        self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=int(self.hotel_controls.hotel_card[1:]), state=state))
        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1)
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)

    def test_controls(self):
        # test DND and room service
        self.hotel_controls.input_ports[self.hotel_controls.hotel_card] = 10 # rapid reading
        self.sync_board()

        # Make sure card is in
        self.set_card(state=1)

        # turn buttons on
        self.hotel_controls.on_controller_data({"do_not_disturb": 1, "room_service": 1})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1)
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.do_not_disturb_port[1:]))).state == 1
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.room_service_port[1:]))).state == 1
        assert self.hotel_controls.get_state()["do_not_disturb"] == 1 and self.hotel_controls.get_state()["room_service"] == 1 and self.hotel_controls.get_state()["card"] == 1 and self.hotel_controls.get_state()["power"] == 1

        self.is_board_synced()

        # turn buttons off
        self.hotel_controls.on_controller_data({"do_not_disturb": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1)
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.do_not_disturb_port[1:]))).state == 0
        assert self.hotel_controls.get_state()["do_not_disturb"] == 0 and self.hotel_controls.get_state()["room_service"] == 1 and self.hotel_controls.get_state()["card"] == 1 and self.hotel_controls.get_state()["power"] == 1

        self.is_board_synced()

        self.hotel_controls.on_controller_data({"room_service": 0})
        self.core.blueprint.update(1)
        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1)
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.room_service_port[1:]))).state == 0
        assert self.hotel_controls.get_state()["do_not_disturb"] == 0 and self.hotel_controls.get_state()["room_service"] == 0 and self.hotel_controls.get_state()["card"] == 1 and self.hotel_controls.get_state()["power"] == 1

        self.is_board_synced()

    def test_card(self):
        # test DND and room service
        self.hotel_controls.input_ports[self.hotel_controls.hotel_card] = 10 # rapid reading
        self.sync_board()

        # Make sure card is in
        self.set_card(state=1)
        assert self.hotel_controls.card_in == 1 and self.hotel_controls.power == 1
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.power_port[1:]))).state == 1

        self.hotel_controls.sleep = Mock()
        self.hotel_controls.wake_up = Mock()

        # Remove card
        self.set_card(state=0)
        assert self.hotel_controls.card_in == 0

        # multiple updates to make sure sleep/wakeup are not spammed
        self.core.blueprint.update(10000000) # assume a long time passed
        self.core.blueprint.update(20000000) # assume a long time passed
        self.core.blueprint.update(30000000) # assume a long time passed
        self.core.blueprint.update(40000000) # assume a long time passed

        time.sleep(self.SOCKET_LAG)

        # Now power should go out
        assert self.hotel_controls.sleep.call_count == 1
        assert self.hotel_controls.wake_up.call_count == 0
        assert self.hotel_controls.card_in == 0 and self.hotel_controls.power == 0
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.power_port[1:]))).state == 0

        self.hotel_controls.sleep = Mock()
        self.hotel_controls.wake_up = Mock()

        # put card back in
        self.set_card(state=1)
        assert self.hotel_controls.card_in == 1

        # multiple updates to make sure sleep/wakeup are not spammed
        self.core.blueprint.update(50000000) # assume a long time passed
        self.core.blueprint.update(60000000) # assume a long time passed
        self.core.blueprint.update(70000000) # assume a long time passed
        self.core.blueprint.update(80000000) # assume a long time passed

        time.sleep(self.SOCKET_LAG)

        # Now power should go out
        assert self.hotel_controls.sleep.call_count == 0
        assert self.hotel_controls.wake_up.call_count == 1
        assert self.hotel_controls.card_in == 1 and self.hotel_controls.power == 1
        assert self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=int(self.hotel_controls.power_port[1:]))).state == 1

