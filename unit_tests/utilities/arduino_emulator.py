import grpc
import testing_utils

class ArduinoEmulator(object):
    ARDUINO_EMULATOR_ADDRESS = "0.0.0.0:5001"

    def initialize(self, base_framework):
        channel = grpc.insecure_channel(self.ARDUINO_EMULATOR_ADDRESS)
        self.emu = testing_utils.ArduinoStub(channel)
        self.emu.ResetPins(testing_utils.Empty())
        self.base_framework = base_framework
        self.core = base_framework.core

    def sync_board(self):
        self.core.update(1)
        self.connected_boards = list(self.core.hw_manager.connected_controllers.values())
        assert len(self.connected_boards) == 1
        self.base_framework.wait_for_condition(lambda _: len(self.connected_boards) == 1 and self.connected_boards[0].is_in_sync())

    def is_board_synced(self):
        return len(self.connected_boards) == 1 and self.connected_boards[0].is_in_sync()

    def set_pin(self, type, index, state):
        self.emu.SetPinState(testing_utils.PinAndState(type=type, index=index, state=state))

    def get_pin(self, type, index):
        return self.emu.GetPinState(testing_utils.Pin(type=type, index=index)).state

    def get_isr_state(self):
        state = self.emu.GetISRState(testing_utils.Empty())
        return (state.full_period, state.wavelength, state.sync)

    def get_isr_pin(self, index):
        return self.emu.GetISRPinState(testing_utils.ISRPin(index=index)).state

    def set_temp(self, temp):
        self.emu.SetTemperatureSensor(testing_utils.Temperature(temp=temp))
