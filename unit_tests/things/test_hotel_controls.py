from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.full_system import FullSystem
from config.general_config import GENERAL_CONFIG

from things.hotel_controls import HotelControls

import time
import testing_utils
from unittest.mock import Mock

class TestHotelControls(BaseTestFramework):
    def setup(self):
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/hotel_controls.json"
        super(TestHotelControls, self).setup()
        self.system = FullSystem(self)

        self.things = self.core.blueprint.get_things()
        self.hotel_controls = self.things[0]

    def teardown(self):
        self.system.destroy()
        super(TestHotelControls, self).teardown()

    def set_card(self, state=1):
    	self.hotel_controls.card_in = 1 - state
    	self.system.arduino_emulator.set_pin(type=0, index=int(self.hotel_controls.hotel_card[1:]), state=state)
    	self.wait_for_condition(lambda self: self.hotel_controls.get_state()["card"] == state)

    def test_controls(self):
        # test DND and room service
        self.hotel_controls.input_ports[self.hotel_controls.hotel_card] = 10 # rapid reading
        self.system.arduino_emulator.sync_board()

        # Make sure card is in
        self.set_card(state=1)

        # turn buttons on
        self.hotel_controls.set_state({"do_not_disturb": 1, "room_service": 1})
        self.wait_for_condition(lambda self:
        	self.hotel_controls.get_state()["do_not_disturb"] == 1 and
        	self.hotel_controls.get_state()["room_service"] == 1 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.do_not_disturb_port[1:])) == 1 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.room_service_port[1:])) == 1
        )

        assert self.system.arduino_emulator.is_board_synced()

        # turn buttons off
        self.hotel_controls.set_state({"do_not_disturb": 0})
        self.wait_for_condition(lambda self:
        	self.hotel_controls.get_state()["do_not_disturb"] == 0 and
        	self.hotel_controls.get_state()["room_service"] == 1 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.do_not_disturb_port[1:])) == 0 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.room_service_port[1:])) == 1
        )

        assert self.system.arduino_emulator.is_board_synced()

        self.hotel_controls.set_state({"room_service": 0})
        self.wait_for_condition(lambda self:
        	self.hotel_controls.get_state()["do_not_disturb"] == 0 and
        	self.hotel_controls.get_state()["room_service"] == 0 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.do_not_disturb_port[1:])) == 0 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.room_service_port[1:])) == 0
        )

        assert self.system.arduino_emulator.is_board_synced()

    def test_card(self):
        # test DND and room service
        self.hotel_controls.input_ports[self.hotel_controls.hotel_card] = 10 # rapid reading
        self.system.arduino_emulator.sync_board()

        # Make sure card is in
        self.set_card(state=1)
        assert self.hotel_controls.card_in == 1 and self.hotel_controls.power == 1
        assert self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.power_port[1:])) == 1

        self.hotel_controls.sleep = Mock()
        self.hotel_controls.wake_up = Mock()

        # Remove card
        self.set_card(state=0)
        assert self.hotel_controls.card_in == 0

        # multiple updates to make sure sleep/wakeup are not spammed
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)

        # Now power should go out
        self.wait_for_condition(lambda self:
        	self.hotel_controls.sleep.call_count == 1 and
        	self.hotel_controls.wake_up.call_count == 0 and
        	self.hotel_controls.card_in == 0 and
        	self.hotel_controls.power == 0 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.power_port[1:])) == 0
        )

        self.hotel_controls.sleep = Mock()
        self.hotel_controls.wake_up = Mock()

        # put card back in
        self.set_card(state=1)
        assert self.hotel_controls.card_in == 1

        # multiple updates to make sure sleep/wakeup are not spammed
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)
        self.current_fake_time += 10000000
        self.core.update(self.current_fake_time)

        # Now power should come back
        self.wait_for_condition(lambda self:
	        self.hotel_controls.sleep.call_count == 0 and
	        self.hotel_controls.wake_up.call_count == 1 and
	        self.hotel_controls.card_in == 1 and
	        self.hotel_controls.power == 1 and
        	self.system.arduino_emulator.get_pin(type=0, index=int(self.hotel_controls.power_port[1:])) == 1
        )

