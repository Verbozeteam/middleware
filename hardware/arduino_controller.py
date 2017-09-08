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
    def __init__(self):
        pass

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
