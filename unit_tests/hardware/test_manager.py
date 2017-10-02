# enable the simulation Arduino mode
from config.general_config import GENERAL_CONFIG
from config.hardware_config import HARDWARE_CONFIG
GENERAL_CONFIG.SIMULATE_ARDUINO = True

from middleware import Core
from things.thing import Thing

import time
import grpc
import testing_utils

class BaseArduinoTestUtil(object):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5001"
    SOCKET_LAG = 0.1 # assume 100ms lag until things reach arduino

    def setup(self):
        #
        # Setup the Arduino emulator
        #
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.arduino_emu = testing_utils.ArduinoStub(channel)
        self.arduino_emu.ResetPins(testing_utils.Empty())

        #
        # Setup the system
        #
        HARDWARE_CONFIG.LEGACY_MODE = False # make sure we are not in legacy mode
        self.core = Core()

    def sync_controller(self):
        self.core.hw_manager.update(1)
        self.connected_controllers = list(self.core.hw_manager.controller_types["arduino"][1].values())
        assert len(self.connected_controllers) == 1
        fake_time = 2
        while not self.connected_controllers[0].is_in_sync():
            self.core.hw_manager.update(fake_time)
            fake_time += 1
            assert fake_time < 30000 # virtual 30 seconds
        self.is_controller_synced()

    def is_controller_synced(self):
        assert self.connected_controllers[0].is_in_sync()

class TestHardwareManager(BaseArduinoTestUtil):
    NUM_DIGITAL_PINS = 53
    NUM_ANALOG_PINS = 16

    class CustomThing(Thing):
        def __init__(self, blueprint, in_pins, out_pins):
            super(self.__class__, self).__init__(blueprint, {})
            self.input_ports = dict(in_pins)
            self.output_ports = dict(out_pins)

    def test_arduino_connection(self):
        self.sync_controller()

    def test_all_digital_outputs(self):
        # initialize the Things in the blueprint to be all digital outputs
        digital_things = list(map(lambda i: TestHardwareManager.CustomThing(self.core.blueprint, [], [("d"+str(i), 1)]), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.get_things = lambda: digital_things

        self.sync_controller()

        # turn all on
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.core.hw_manager.on_command("d"+str(i), 1)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == 1)

        self.is_controller_synced()

        # turn all off
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.core.hw_manager.on_command("d"+str(i), 0)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == 0)

        self.is_controller_synced()

        # turn half on
        for i in range(0, int(self.NUM_DIGITAL_PINS / 2)):
            self.core.hw_manager.on_command("d"+str(i), 1)
        time.sleep(self.SOCKET_LAG)
        for i in range(0, self.NUM_DIGITAL_PINS):
            expected = 1 if i < int(self.NUM_DIGITAL_PINS / 2) else 0
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == expected)

        self.is_controller_synced()

    def test_all_analog_inputs(self):
        # initialize the Things in the blueprint to be all inputs (analog and digital)
        analog_things = list(map(lambda i: TestHardwareManager.CustomThing(self.core.blueprint, [("a"+str(i), 10)], []), range(0, self.NUM_ANALOG_PINS)))
        digital_things = list(map(lambda i: TestHardwareManager.CustomThing(self.core.blueprint, [("d"+str(i), 10)], []), range(0, self.NUM_DIGITAL_PINS)))
        self.core.blueprint.get_things = lambda: analog_things + digital_things

        for i in range(0, self.NUM_ANALOG_PINS):
            self.arduino_emu.SetPinState(testing_utils.PinAndState(type=1, index=i, state=i))
        for i in range(0, self.NUM_DIGITAL_PINS):
            self.arduino_emu.SetPinState(testing_utils.PinAndState(type=0, index=i, state=1))

        self.sync_controller()

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

        print (reading_map)

        for i in range(0, self.NUM_ANALOG_PINS):
            assert reading_map["a"+str(i)][0] == reading_map["a"+str(i)][1]
        for i in range(0, self.NUM_DIGITAL_PINS):
            assert reading_map["d"+str(i)][0] == reading_map["d"+str(i)][1]

        self.is_controller_synced()

    def test_pwm_outputs(self):
        # initialize the Things in the blueprint to be PWM outputs for pins 4-8
        digital_things = list(map(lambda i: TestHardwareManager.CustomThing(self.core.blueprint, [], [("d"+str(i), 2)]), range(4, 8)))
        self.core.blueprint.get_things = lambda: digital_things

        self.sync_controller()

        # turn all on
        for i in range(4, 8):
            self.core.hw_manager.on_command("d"+str(i), i*4)
        time.sleep(self.SOCKET_LAG)
        for i in range(4, 8):
            assert(self.arduino_emu.GetPinState(testing_utils.Pin(type=0, index=i)).state == i * 4)

        self.is_controller_synced()

