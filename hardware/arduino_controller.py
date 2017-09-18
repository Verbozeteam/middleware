from hardware.controller_base import HardwareController

import struct

# 8-byte sequence that represents a sequence sent periodically by the Arduino
# to sync the communication
SYNC_SEQUENCE = bytearray([254, 6, 252, 11, 76, 250, 250, 255])

#
# Represents the current state of a connected Arduino. The state includes the
# values on all the input pins of the Arduino
#
class ArduinoState(object):
    # Represents the state of a pin on the Arduino
    class Pin(object):
        class MODE:
            UNKNOWN = 0
            OUTPUT = 1
            INPUT = 2

        def __init__(self, mode=MODE.UNKNOWN, value=0):
            self.mode = mode
            self.value = value

    def __init__(self):
        self.analog_pins = []
        self.digital_pins = []

    # Set an analog pin's state
    # value Value to set the pin to
    # mode  Mode to set the pin to
    def set_analog_pin(self, index, value=None, mode=None):
        num_missing_pins = (index - len(self.analog_pins)) + 1
        for pin in num_missing_pins:
            self.analog_pins.append(ArduinoState.Pin())
        if value:
            self.analog_pins[index].value = value
        if mode:
            self.analog_pins[index].mode = mode

    # Set a digital pin's state
    # value Value to set the pin to
    # mode  Mode to set the pin to
    def set_digital_pin(self, index, value=None, mode=None):
        num_missing_pins = (index - len(self.digital_pins)) + 1
        for pin in num_missing_pins:
            self.digital_pins.append(ArduinoState.Pin())
        if value:
            self.digital_pins[index].value = value
        if mode:
            self.digital_pins[index].mode = mode

    def on_message(self, message_type, message):
        return True

#
# An Arduino controller
#
class ArduinoController(HardwareController):
    def __init__(self, comport):
        super(self.__class__, self).__init__(comport, baud=9600)
        self.read_buffer = bytearray([])
        self.wait_for_sync = True
        self.sync_send_timer = 0
        self.sync_send_period = 1
        self.state = ArduinoState()

    # Synchronizes the read buffer with the Arduino if its not already in sync.
    # returns True if the buffer is in sync, False otherwise
    def sync_input_buffer(self, cur_time_s):
        global SYNC_SEQUENCE
        if self.sync_send_timer >= cur_time_s:
            self.sync_send_timer = cur_time_s + self.sync_send_period
            self.serial_port.write(SYNC_SEQUENCE)

        if self.wait_for_sync:
            self.sync_send_period = 1
            found_sync = False
            for sync_start in range(0, len(self.read_buffer) - len(SYNC_SEQUENCE)):
                is_sync_start = True # Whether sync_start is where a sync sequence starts
                for sync_index in range(len(SYNC_SEQUENCE)):
                    if self.read_buffer[sync_start+sync_index] != SYNC_SEQUENCE[sync_index]:
                        is_sync_start = False # Not the right sequence
                        break
                if is_sync_start:
                    found_sync = True
                    break

            if found_sync:
                self.read_buffer = self.read_buffer[sync_start+len(SYNC_SEQUENCE):]
                self.wait_for_sync = False
                self.sync_send_period = 10
            else:
                # truncate the beginning of the read buffer
                if len(self.read_buffer) > len(SYNC_SEQUENCE):
                    self.read_buffer = self.read_buffer[len(self.read_buffer)-len(SYNC_SEQUENCE):]
                return False

        return True

    # Parse the read buffer's messages and interpret them. If any message
    # corruption is detected, it will set wait_for_sync to True.
    # returns True if the connection should continue, False otherwise
    def process_read_buffer(self):
        while len(self.read_buffer) > 2:
            (msg_type, msg_len) = struct.unpack(self.read_buffer, 'ii')
            if len(self.read_buffer) >= 2 + msg_len:
                msg = self.read_buffer[2:2+msg_len]
                self.read_buffer = self.read_buffer[2+msg_len:]
                if not self.on_message(msg_type, msg):
                    # Failed to understand the message, need to sync again
                    self.wait_for_sync = True
                    break
        return True

    # Called when a message has been found on the read buffer.
    # message_type Message type
    # message      The contents of the message
    # returns      True if the message is valid, False otherwise
    def on_message(self, message_type, message):
        global SYNC_SEQUENCE
        if message_type == SYNC_SEQUENCE[0]: # This message is just a SYNC sequence
            return len(message) == 6 and message == SYNC_SEQUENCE[2:] # must be valid
        return self.state.on_message(message_type, message)

    def update(self, cur_time_s):
        num_bytes = self.serial_port.in_waiting
        if num_bytes > 0:
            b = self.serial_port.read(num_bytes)
            self.read_buffer += b

        if self.sync_input_buffer(cur_time_s):
            return self.process_read_buffer()

        return True

    # To identify an arduino on a COM port, find "arduino" anywhere in the
    # hardware description
    @staticmethod
    def identify(ports):
        ret = []
        for p in ports:
            for attr in dir(p):
                a = getattr(p, attr)
                if type(a) == type("") and "arduino" in a.lower():
                    ret.append(p.serial_number)
        return ret

#
# A legacy Arduino controller that uses the old protocol for communication
#
class ArduinoLegacyController(ArduinoController):
    def __init__(self, comport):
        super(self.__class__, self).__init__(comport, baud=9600)
        self.read_buffer = bytearray([])
        self.state = ArduinoState()
        self.BEGINNING_BYTE = 254
        self.ENDING_BYTE = 255

    # Syncing the controller is handled while reading the buffer
    def sync_input_buffer(self, cur_time_s):
        return True

    # Parse the read buffer's messages and interpret them. If any message
    # corruption is detected, it will discard the message(s) until a new
    # beginning is detected
    # returns True if the connection should continue, False otherwise
    def process_read_buffer(self):
        while True:
            beg_idx = self.read_buffer.index(self.BEGINNING_BYTE)
            if beg_idx == -1:
                break
            self.read_buffer = self.read_buffer[beg_idx:]
            end_idx = self.read_buffer.index(self.ENDING_BYTE)
            if end_idx == -1:
                break
            msg = self.read_buffer[beg_idx+1:end_idx-1]
            self.read_buffer = self.read_buffer[end_idx+1:]
            self.on_message(msg)
        return True

    # Called when a message has been found on the read buffer.
    # message      The contents of the message
    # returns      True if the message is valid, False otherwise
    def on_message(self, message):
        try:
            base_idx = 0
            ACs = [] # list of (AC fan speed, AC Set point * 2.0f, temperate)
            num_acs = message[base_idx]
            base_idx += 1
            for ac in num_acs:
                ACs.append((messages[base_idx+0*num_acs+ac], messages[base_idx+1*num_acs+ac], messages[base_idx+2*num_acs+ac]))
            base_idx += 3*num_acs
            num_dimmers = message[base_idx]
            base_idx += 1
            dimmers = list(message[base_idx:base_idx+num_dimmers])
            base_idx += num_dimmers
            num_lights = message[base_idx]
            base_idx += 1
            lights = list(message[base_idx:base_idx+num_lights])
            base_idx += num_lights
            num_curtains = message[base_idx]
            base_idx += 1
            if base_idx != len(message):
                raise 1 # invalid message...

            return True
        except:
            return False

