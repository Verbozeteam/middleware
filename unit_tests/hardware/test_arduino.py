# enable the simulation Arduino mode
from unit_tests.hardware.arduino_emulator_tests import BaseArduinoEmulatorTestUtil

from config.hardware_config import HARDWARE_CONFIG

from things.thing import Thing

import time
import testing_utils

class TestArduinoController(BaseArduinoEmulatorTestUtil):
    NUM_DIGITAL_PINS = 53
    NUM_ANALOG_PINS = 16

    class CustomThing(Thing):
        def __init__(self, blueprint, in_pins, out_pins):
            super(self.__class__, self).__init__(blueprint, {})
            self.input_ports = dict(in_pins)
            self.output_ports = dict(out_pins)

    def test_arduino_connection(self):
        self.sync_board()

    def test_all_digital_outputs(self):
        # initialize the Things in the blueprint to be all digital outputs
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [], [("d"+str(i), 1)]), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.get_things = lambda: digital_things

        self.sync_board()

        # turn all on
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.core.hw_manager.on_command("d"+str(i), 1)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == 1)

        self.is_board_synced()

        # turn all off
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.core.hw_manager.on_command("d"+str(i), 0)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == 0)

        self.is_board_synced()

        # turn half on
        for i in range(0, int(self.NUM_DIGITAL_PINS / 2)):
            self.core.hw_manager.on_command("d"+str(i), 1)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            expected = 1 if i < int(self.NUM_DIGITAL_PINS / 2) else 0
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == expected)

        self.core.hw_manager.update(1000001)
        self.is_board_synced()

    def test_all_analog_inputs(self):
        # initialize the Things in the blueprint to be all inputs (analog and digital)
        analog_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [("a"+str(i), 10)], []), range(0, self.NUM_ANALOG_PINS)))
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [("d"+str(i), 10)], []), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.get_things = lambda: analog_things + digital_things

        for i in range(0, self.NUM_ANALOG_PINS):
            self.arduino_emu.SetPinState(testing_utils.PinAndState(type=1, index=i, state=i))
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=i, state=1))

        self.sync_board()

        reading_map = {}
        for i in range(0, self.NUM_ANALOG_PINS):
            reading_map["a"+str(i)] = [-1, i]
        for i in range(0, self.NUM_DIGITAL_PINS):
            reading_map["d"+str(i)] = [-1, 1]

        def on_hardware_data(port, value):
            assert port in reading_map
            assert reading_map[port][1] == value
            reading_map[port][0] = value

        self.core.blueprint.on_hardware_data = on_hardware_data

        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1000000)

        for i in range(0, self.NUM_ANALOG_PINS):
            assert reading_map["a"+str(i)][0] == reading_map["a"+str(i)][1]
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert reading_map["d"+str(i)][0] == reading_map["d"+str(i)][1]

        self.core.hw_manager.update(1000001)
        self.is_board_synced()

    def test_pwm_outputs(self):
        # initialize the Things in the blueprint to be PWM outputs for pins 4-8
        digital_things = list(map(lambda i: TestArduinoController.CustomThing(self.core.blueprint, [], [("d"+str(i), 2)]), range(4, 8)))
        self.core.blueprint.get_things = lambda: digital_things

        self.sync_board()

        # set PWM outputs
        for i in range(4, 8):
            self.core.hw_manager.on_command("d"+str(i), i*4)
        time.sleep(self.SOCKET_LAG)
        for i in range(4, 8):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == i * 4)

        self.core.hw_manager.update(1000001)
        self.is_board_synced()

    def test_temperature_sensor(self):
        things = [TestArduinoController.CustomThing(self.core.blueprint, [("v0", 10)], [])]
        things[0].virtual_port_data = [[0, 0]] # 0: central AC virtual pin, 0: temp index 0
        self.core.blueprint.get_things = lambda: things

        self.arduino_emu.SetTemperatureSensor(testing_utils.Temperature(temp=25.0))

        self.sync_board()

        got_reading = {"result": False}
        def on_hardware_data(port, value):
            assert port == "v0"
            assert value == 50 # reading is always twice as actual temperature
            got_reading["result"] = True

        self.core.blueprint.on_hardware_data = on_hardware_data

        time.sleep(self.SOCKET_LAG)
        self.core.hw_manager.update(1000000)

        assert got_reading["result"] == True

        self.is_board_synced()

