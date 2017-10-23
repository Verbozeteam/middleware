from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.arduino_emulator import ArduinoEmulator
from config.hardware_config import HARDWARE_CONFIG

from things.thing import Thing

from unittest.mock import Mock, call

class TestArduinoController(BaseTestFramework):
    NUM_DIGITAL_PINS = 53
    NUM_ANALOG_PINS = 16

    class CustomThing(Thing):
        def __init__(self, blueprint, in_pins, out_pins):
            super(self.__class__, self).__init__(blueprint, {})
            self.id = str(in_pins) + "-" + str(out_pins)
            self.input_ports = dict(in_pins)
            self.output_ports = dict(out_pins)

    class CustomRoom(object):
        def __init__(self, things):
            self.things = dict(map(lambda t: (t.id, t), things))

    def setup(self):
        HARDWARE_CONFIG.LEGACY_MODE = False # make sure we are not in legacy mode
        super(TestArduinoController, self).setup()
        self.arduino = ArduinoEmulator()
        self.arduino.initialize(self)

    def test_arduino_connection(self):
        self.arduino.sync_board()

    def test_all_digital_outputs(self):
        # initialize the Things in the blueprint to be all digital outputs
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [], [("d"+str(i), 1)]), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.rooms = [TestArduinoController.CustomRoom(digital_things)]

        self.arduino.sync_board()

        # turn all on
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.arduino.connected_boards[0].set_port_value("d"+str(i), 1)
        def lights_are_on(self):
            for i in range(0, self.NUM_DIGITAL_PINS):
                if self.arduino.get_pin(type=0, index=i) != 1:
                    return False
            return True
        self.wait_for_condition(lights_are_on)

        assert self.arduino.is_board_synced()

        # turn all off
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.arduino.connected_boards[0].set_port_value("d"+str(i), 0)
        def lights_are_off(self):
            for i in range(0, self.NUM_DIGITAL_PINS):
                if self.arduino.get_pin(type=0, index=i) != 0:
                    return False
            return True
        self.wait_for_condition(lights_are_off)

        assert self.arduino.is_board_synced()

        # turn half on
        for i in range(0, int(self.NUM_DIGITAL_PINS / 2)):
            self.arduino.connected_boards[0].set_port_value("d"+str(i), 1)
        def lights_half_on(self):
            for i in range(0, self.NUM_DIGITAL_PINS):
                expected = 1 if i < int(self.NUM_DIGITAL_PINS / 2) else 0
                if self.arduino.get_pin(type=0, index=i) != expected:
                    return False
            return True
        self.wait_for_condition(lights_half_on)

        assert self.arduino.is_board_synced()

    def test_all_analog_inputs(self):
        # initialize the Things in the blueprint to be all inputs (analog and digital)
        analog_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [("a"+str(i), 10)], []), range(0, self.NUM_ANALOG_PINS)))
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [("d"+str(i), 10)], []), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.rooms = [TestArduinoController.CustomRoom(analog_things + digital_things)]

        for i in range(0, self.NUM_ANALOG_PINS):
            self.arduino.set_pin(type=1, index=i, state=i)
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.arduino.set_pin(type=0, index=i, state=1)

        self.arduino.sync_board()

        self.core.hw_manager.on_port_update = Mock()

        def all_readings_found(self):
            for i in range(0, self.NUM_ANALOG_PINS):
                if call(self.arduino.connected_boards[0], "a"+str(i), i) not in self.core.hw_manager.on_port_update.mock_calls:
                    return False
            for i in range(0, self.NUM_DIGITAL_PINS):
                if call(self.arduino.connected_boards[0], "d"+str(i), 1) not in self.core.hw_manager.on_port_update.mock_calls:
                    return False
            return True

        self.wait_for_condition(all_readings_found)

        assert self.arduino.is_board_synced()

    def test_pwm_outputs(self):
        # initialize the Things in the blueprint to be PWM outputs for pins 4-8
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [], [("d"+str(i), 2)]), range(4, 8)))
        self.core.blueprint.rooms = [TestArduinoController.CustomRoom(digital_things)]

        self.arduino.sync_board()

        # set PWM outputs
        for i in range(4, 8):
            self.arduino.connected_boards[0].set_port_value("d"+str(i), i*4)

        def all_pwms_correct(self):
            for i in range(4, 8):
                if self.arduino.get_pin(type=0, index=i) != i * 4:
                    return False
            return True

        self.wait_for_condition(all_pwms_correct)

        assert self.arduino.is_board_synced()

    def test_temperature_sensor(self):
        things = [TestArduinoController.CustomThing(self.core.blueprint, [("v0", 10)], [])]
        things[0].virtual_port_data = [[0, 0]] # 0: central AC virtual pin, 0: temp index 0
        self.core.blueprint.rooms = [TestArduinoController.CustomRoom(things)]

        self.arduino.set_temp(temp=26.0)

        self.arduino.sync_board()

        self.core.hw_manager.on_port_update = Mock()

        def temp_read(self):
            # reading will be * 4 (according to protocol)
            return call(self.arduino.connected_boards[0], "v0", 26*4) in self.core.hw_manager.on_port_update.mock_calls

        self.wait_for_condition(temp_read)

        assert self.arduino.is_board_synced()

