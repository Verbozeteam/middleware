from unit_tests.controllers.test_controllers import FakeController
from unit_tests.hardware.test_arduino_emulator import ArduinoEmulator

class FullSystem(object):
    def __init__(self, base_framework, num_controllers=1):
        self.base_framework = base_framework
        self.core = base_framework.core

        self.arduino_emulator = ArduinoEmulator()
        self.arduino_emulator.initialize(self.base_framework)

        self.core.update(1)

        self.fake_controllers = []
        for i in range(0, num_controllers):
            # connect the fake controller (in a separate thread)
            c = FakeController(self.core, self.core.ctrl_manager.tcp_socket_connection_manager)
            c.connect()
            self.fake_controllers.append(c)

    def destroy(self):
        for c in self.fake_controllers:
            c.disconnect()
        self.fake_controllers = []

