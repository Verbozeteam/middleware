#
# Zigbee controller is implemented by making a single main controller that manages
# all zigbees. Each zigbee it registers has the following characteristics:
#  - The Zigbee must have an address 0x2 - 0xFE
#  - The Zigbee will be delegated all ports with index [(address-2) * 10 to (address-1) * 10[
#  - The Zigbee will map each port (e.g. d22) to 0-10 range local to the Arduino on the other
#    side of the zigbee (e.g. d2)
#  - The data read from the Zigbee will have their ports mapped opposite to the above mapping
#  - The Zigbee will constantly be in sync with the zigbee controller similar to normal arduinos
#  - The Zigbee will mimic the behavior of a normal Arduino controller except the above mapping
#    and wrapping data sent and received in Zigbee headers
# Communication with zigbees is done by connecting to a Zigbee on the serial port using API mode
# with address 0x1.
#
# * ALL ZIGBEE CONTROLLERS CONNECTED MUST HAVE ADDRESSES 0x2-0xFE
# * ALL ZIGBEE CONTROLLERS CONNECTED MUST ASSUME THE MASTER'S ADDRESS IS 0x1
#

from hardware.controller_base import HardwareController
from hardware.arduino_controller import ArduinoController, ArduinoProtocol
from logs import Log

import struct

DELIMITER = 0x7E
ILLEGAL_CHARACTERS = [0x7E, 0x7D, 0x11, 0x13]
ESCAPE_CHARACTER = 0x7D
UNESCAPE_CHARACTER = 0x20

class RemoteZigbee(ArduinoController):
    def __init__(self, master, addr):
        self.master = master
        self.address = addr
        self.hw_manager = master.hw_manager
        self.my_pin_offset = -(addr-2) * 10 # zigbee address 0x2 takes pins 0-9, zigbee address 0x3 tages 10-19, etc...

        self.read_buffer = bytearray([])
        self.half_sync = False
        self.full_sync = False
        self.sync_send_timer = 0
        self.sync_send_period = 1
        self.receive_timeout = -1
        self.is_initialized = False

    def write_to_fd(self, data):
        self.master.zigbeeTx(self.address, data)

    def update(self, cur_time_s):
        try:
            if self.receive_timeout < 0:
                self.receive_timeout = cur_time_s + 13

            if cur_time_s > self.receive_timeout:
                Log.warning("ArduinoController::update() timed out")
                return False # haven't received anything in a long time!

            if self.sync_input_buffer(cur_time_s):
                return self.process_read_buffer()
        except Exception as e:
            Log.error("", exception=True)

        return True

    def initialize_board(self):
        ArduinoProtocol.set_pin_ranges(self.my_pin_offset, 10, self.my_pin_offset, 10, self.my_pin_offset, 10)
        super(RemoteZigbee, self).initialize_board()
        ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)

    def set_port_value(self, port, value):
        if self.is_in_sync():
            ArduinoProtocol.set_pin_ranges(self.my_pin_offset, 10, self.my_pin_offset, 10, self.my_pin_offset, 10)
            self.write_to_fd(ArduinoProtocol.create_set_pin_output(port, value))
            ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)

    def on_read_ready(self, data, cur_time_s):
        try:
            self.read_buffer += data
            self.receive_timeout = cur_time_s + 13
        except:
            Log.error("RemoteZigbee::on_read_ready() failed", exception=True)
            return False
        return True

    def on_message(self, message_type, message):
        ArduinoProtocol.set_pin_ranges(-self.my_pin_offset, 10, -self.my_pin_offset, 10, -self.my_pin_offset, 10)
        ret = super(RemoteZigbee, self).on_message(message_type, message)
        ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)
        return ret

#
# An Arduino controller
#
class ZigbeeController(HardwareController):
    def __init__(self, hw_manager, comport, fake_serial_port=None):
        self.m_remoteZigbees = {} # address -> Remote zigbees connected to this zigbee
        self.m_frameNumber = 1
        self.m_readBuffer = bytearray([])
        Log.hammoud("Zigbee was found!")
        super(ZigbeeController, self).__init__(hw_manager, comport, baud=9600, fake_serial_port=fake_serial_port)

        # find target addresses
        things = hw_manager.core.blueprint.get_things()
        for T in things:
            all_ports = list(T.input_ports.keys()) + list(T.output_ports.keys())
            for p in all_ports:
                port_index = int(p[1:])
                zigbee_address = int(port_index / 10) + 2
                self.addRemote(zigbee_address)

    def addRemote(self, addr):
        if addr not in self.m_remoteZigbees:
            self.m_remoteZigbees[addr] = RemoteZigbee(self, addr)

    def initiateDiscovery(self):
        self.zigbeeTx(0xFFFF, [ord('D')], 1);

    def zigbeeTx(self, addrTo, data):
        # Create an API frame targeting addrTo and escape and stuff
        # [0x01, frame, LEN MSB, LEN LSB, DATA]
        if len(data) > 0:
            buf = bytearray([0x01, self.m_frameNumber, (addrTo >> 8) & 0xFF, addrTo & 0xFF]) + bytearray(data)
            self.m_frameNumber += 1
            if self.m_frameNumber == 256:
                self.m_frameNumber = 1

            self.zigbeeAPICall(buf);

    def zigbeeChecksum(self, data):
        return 0xFF - (sum(list(data)) % 256)

    def zigbeeCheckChecksum(self, data, checksum):
        s = checksum
        for d in data:
            s = (s + d) & 0xFF
        if s != 0xFF:
            Log.warning("checksum failed: {} {} {}".format(s, list(map(lambda d: format(d, '02x'), data)), checksum))
        return s == 0xFF

    def zigbeeEscape(self, arr):
        global ILLEGAL_CHARACTERS, UNESCAPE_CHARACTER
        newarr = []
        for b in arr:
            if b in ILLEGAL_CHARACTERS:
                newarr += [0x7D, b ^ UNESCAPE_CHARACTER]
            else:
                newarr += [b]
        return bytearray(newarr)

    def zigbeeAPICall(self, cmd):
        global DELIMITER
        msb = (len(cmd) >> 8) & 0xFF
        lsb = (len(cmd)     ) & 0xFF
        checksum = self.zigbeeChecksum(cmd)

        self.write_to_fd(bytearray([DELIMITER]) + self.zigbeeEscape([msb, lsb] + list(cmd) + [checksum]))

    def update(self, cur_time_s):
        try:
            if not super(ZigbeeController, self).update(cur_time_s):
                return False

            if not self.process_read_buffer(cur_time_s):
                return False

            to_be_removed = []
            for remote in self.m_remoteZigbees.values():
                if not remote.update(cur_time_s):
                    to_be_removed.append(remote.address)

            for remote in to_be_removed:
                del self.m_remoteZigbees[remote]
        except:
            Log.error("", exception=True)

        return True

    def onZigbeeFrame(self, frame, checksum, cur_time_s):
        if self.zigbeeCheckChecksum(frame, checksum):
            cmdID = frame[0]
            if cmdID == 0x8A and len(frame) == 2: # modem status
                pass
            elif cmdID == 0x89 and len(frame) >= 3: # Tx status
                pass
            elif cmdID == 0x81 and len(frame) >= 5: # Rx from a 16 bit address
                addr_msb = frame[1]
                addr_lsb = frame[2]
                rssi = frame[3]
                options = frame[4]
                data = frame[5:]
                addr = (addr_msb << 8) | addr_lsb
                if addr in self.m_remoteZigbees:
                    self.m_remoteZigbees[addr].on_read_ready(data, cur_time_s)

    def process_read_buffer(self, cur_time_s):
        global ESCAPE_CHARACTER, UNESCAPE_CHARACTER
        # find zigbee frames in self.m_readBuffer and interpret them
        # send zigbee-specific stuff to the respective self.m_remoteZigbees
        while len(self.m_readBuffer) > 0:
            if self.m_readBuffer[0] != 0x7E:
                print ("-- ", self.m_readBuffer[0])
                self.m_readBuffer = self.m_readBuffer[1:]
            else:
                cur_pos = 1

                if cur_pos >= len(self.m_readBuffer):
                    break
                len_msb = self.m_readBuffer[cur_pos]
                cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break
                if len_msb == ESCAPE_CHARACTER:
                    len_msb = self.m_readBuffer[cur_pos] ^ UNESCAPE_CHARACTER;
                    cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break

                len_lsb = self.m_readBuffer[cur_pos]
                cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break
                if len_lsb == ESCAPE_CHARACTER:
                    len_lsb = self.m_readBuffer[cur_pos] ^ UNESCAPE_CHARACTER;
                    cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break

                content_len = ((len_msb & 0xFF) << 8) | (len_lsb & 0xFF)

                # count escape characters found
                content_and_checksum = bytearray([])
                i = 0;
                while i < content_len + 1: # +1 for checksum
                    if cur_pos >= len(self.m_readBuffer):
                        break
                    content_and_checksum.append(self.m_readBuffer[cur_pos])
                    cur_pos += 1
                    if content_and_checksum[-1] == ESCAPE_CHARACTER:
                        if cur_pos >= len(self.m_readBuffer):
                            break
                        content_and_checksum[-1] = self.m_readBuffer[cur_pos] ^ UNESCAPE_CHARACTER
                        cur_pos += 1
                    i += 1
                if i != content_len + 1:
                    break

                self.m_readBuffer = self.m_readBuffer[cur_pos:]
                self.onZigbeeFrame(content_and_checksum[:content_len], content_and_checksum[-1], cur_time_s)

        return True

    def set_port_value(self, port, value):
        super(ZigbeeController, self).set_port_value(port, value)
        for z in self.m_remoteZigbees.values():
            z.set_port_value(port, value)

    def on_read_ready(self, cur_time_s):
        try:
            b = self.serial_port.read(self.serial_port.in_waiting)
            self.m_readBuffer += b
        except:
            Log.error("ZigbeeController::on_read_ready() failed", exception=True)
            return False
        return True

    # To identify a zigbee on a COM port, find "FT231X USB UART" anywhere in the
    # hardware description
    @staticmethod
    def identify(ports):
        ret = []
        for p in ports:
            for attr in dir(p):
                a = getattr(p, attr)
                if type(a) == type("") and "FT231X USB UART" in a:
                    ret.append(p.serial_number)
                    break
        return ret
