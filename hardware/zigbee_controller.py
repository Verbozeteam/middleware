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
from things.blueprint import RemoteBoard
from logs import Log

import struct
import time

class ZigbeeProtocol:
    DELIMITER = 0x7E
    ILLEGAL_CHARACTERS = [0x7E, 0x7D, 0x11, 0x13]
    ESCAPE_CHARACTER = 0x7D
    UNESCAPE_CHARACTER = 0x20

class RemoteZigbee(ArduinoController):
    def __init__(self, master, addr16, addr64, remoteBoardDefintion):
        self.master = master
        self.address16 = addr16
        self.address64 = addr64
        self.hw_manager = master.hw_manager
        self.definition = remoteBoardDefintion

        self.read_buffer = bytearray([])
        self.half_sync = False
        self.full_sync = False
        self.sync_send_timer = 0
        self.sync_send_period = 1
        self.receive_timeout = -1
        self.is_initialized = False
        
        self.num_allowed_halves = 0
        self.total_bytes_received = 0
        self.max_bytes_per_unit_time = 63
        self.unit_time_seconds = 0.5

    def write_to_fd(self, data):
        self.master.zigbeeTx(self.address16, self.address64, data)

    def update(self, cur_time_s):
        try:
            if self.receive_timeout < 0:
                self.receive_timeout = cur_time_s + 13

            if cur_time_s > self.receive_timeout:
                Log.warning("ArduinoController::update() timed out")
                return False # haven't received anything in a long time!

            if self.sync_input_buffer(cur_time_s):
                return self.process_read_buffer()
        except:
            Log.error("", exception=True)

        return True

    def initialize_board(self):
        ArduinoProtocol.set_pin_ranges(
            -self.definition.digital_port_start_range, self.definition.num_digital_ports,
            -self.definition.analog_port_start_range, self.definition.num_analog_ports,
            -self.definition.virtual_port_start_range, self.definition.num_virtual_ports)
        super(RemoteZigbee, self).initialize_board()
        ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)
        self.master.clear_cache() # clear master cache to allow messages to pass through to self

    def set_port_value(self, port, value):
        if self.is_in_sync():
            ArduinoProtocol.set_pin_ranges(
                -self.definition.digital_port_start_range, self.definition.num_digital_ports,
                -self.definition.analog_port_start_range, self.definition.num_analog_ports,
                -self.definition.virtual_port_start_range, self.definition.num_virtual_ports)
            self.write_to_fd(ArduinoProtocol.create_set_pin_output(port, value))
            ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)

    def on_read_ready(self, data, cur_time_s):
        try:
            self.read_buffer += data
            self.receive_timeout = cur_time_s + 13
            self.total_bytes_received += len(data)
        except:
            Log.error("RemoteZigbee::on_read_ready() failed", exception=True)
            return False
        return True

    def on_message(self, message_type, message):
        ArduinoProtocol.set_pin_ranges(
            -self.definition.digital_port_start_range, self.definition.num_digital_ports,
            -self.definition.analog_port_start_range, self.definition.num_analog_ports,
            -self.definition.virtual_port_start_range, self.definition.num_virtual_ports)
        ret = super(RemoteZigbee, self).on_message(message_type, message)
        ArduinoProtocol.set_pin_ranges(0, -1, 0, -1, 0, -1)
        return ret

#
# An Arduino controller
#
class ZigbeeController(HardwareController):
    def __init__(self, hw_manager, comport, fake_serial_port=None):
        self.m_remoteZigbees = {} # address -> Remote zigbees connected to this zigbee
        self.m_frameNumber = 0
        self.m_maxRetries = 3
        self.m_outboundMessages = {0: (0, 0, None)} # frame # -> (addTo16, attemptsLeft, zigbee command) dictionary. Fill 0 with None to make the frame number unselectible
        self.m_queuedMessages = [] # list of (addr16, addr64, data) tuples that are queued to be sent due to lack of empty frame number
        self.m_readBuffer = bytearray([])
        super(ZigbeeController, self).__init__(hw_manager, comport, baud=9600, fake_serial_port=fake_serial_port)

        Log.info("Zigbee attached, starting setup...")
        self.is_setup = False
        self.setupZigbee()

    def setupZigbee(self):
        time.sleep(1.1)                                                         # wait for command mode listening to start
        self.write_to_fd(bytearray(map(lambda c: ord(c), list('+++'))))         # enter command mode
        self.on_write_ready(0)                                                  # flush out the command
        time.sleep(1.1)                                                         # wait for command mode to activate
        commands = [
            "ATCE 1",           # set as coordinator
            "ATAP 2",           # AP mode -> API mode with escaped characters
            "ATID 1234",        # PanID 0x3332
            "ATNJ FF",          # open join time (@TODO: CHANGE THIS)
            "ATEE 0",           # disable security
            "ATCN",             # end command mode
        ]
        for cmd in commands:
            self.write_to_fd(bytearray(map(lambda c: ord(c), list(cmd+'\r'))))
        self.on_write_ready(0) # flush out all above commands
        ok_status = 'OK\r'.encode('utf-8')
        numAttempts = 10
        while numAttempts > 0 and len(self.m_readBuffer.split(ok_status))-1 != len(commands)+1:
            time.sleep(0.2)
            self.on_read_ready(0)
            numAttempts -= 1

        if len(self.m_readBuffer.split(ok_status))-1 != len(commands)+1:
            Log.error('Failed to setup zigbee: {}'.format(self.m_readBuffer))
        else:
            Log.info('Zigbee setup complete')
            self.m_readBuffer = self.m_readBuffer.replace(ok_status, bytearray([])) # remove status from buffer
            self.is_setup = True

    def addRemote(self, addr16, addr64):
        if addr16 not in self.m_remoteZigbees:
            boardDefinition = self.hw_manager.core.blueprint.get_remote_board(addr64)
            if not boardDefinition:
                Log.warning("Zigbee [0x%x:0x%x] trying to connect but has no board definition" % (addr16, addr64))
                return False
            Log.info("Adding zigbee [0x%x:0x%x]" % (addr16, addr64))
            self.m_remoteZigbees[addr16] = RemoteZigbee(self, addr16, addr64, boardDefinition)
            self.clear_cache() # let cache updates pass through
        return True

    def initiateDiscovery(self):
        self.zigbeeTx(0xFFFE, 0x0000FFFF, [ord('D')])

    def zigbeeTx(self, addrTo16, addrTo64, data):
        addrTo16 = 0xFFFE # this means use the 64 bit address
        # Create an API frame targeting addrTo and escape and stuff
        # [0x10, frameID, broadcastMode, ADDR MSB, ADDR LSB, radius, options, DATA]
        if len(data) > 0:
            startNum = self.m_frameNumber
            self.m_frameNumber = (self.m_frameNumber + 1) % 256
            while self.m_frameNumber in self.m_outboundMessages:
                self.m_frameNumber = (self.m_frameNumber + 1) % 256
                if self.m_frameNumber == startNum: # cannot find a free frame number. queue the message
                    self.m_queuedMessages.append((addrTo16, addrTo64, data))
                    return

            buf = bytearray([0x10, self.m_frameNumber,
                (addrTo64 >> 56) & 0xFF, (addrTo64 >> 48) & 0xFF, (addrTo64 >> 40) & 0xFF, (addrTo64 >> 32) & 0xFF, (addrTo64 >> 24) & 0xFF, (addrTo64 >> 16) & 0xFF, (addrTo64 >> 8) & 0xFF, addrTo64 & 0xFF,
                (addrTo16 >> 8) & 0xFF, addrTo16 & 0xFF,
                0, 0]) + bytearray(data)
            self.m_outboundMessages[self.m_frameNumber] = (addrTo16, self.m_maxRetries, buf)

            Log.hammoud("TXing [{}][To {}]: {}".format(buf[1], "0x%x:0x%x" % (addrTo16, addrTo64), list(buf)))
            self.zigbeeAPICall(buf)

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
        newarr = []
        for b in arr:
            if b in ZigbeeProtocol.ILLEGAL_CHARACTERS:
                newarr += [0x7D, b ^ ZigbeeProtocol.UNESCAPE_CHARACTER]
            else:
                newarr += [b]
        return bytearray(newarr)

    def zigbeeAPICall(self, cmd):
        msb = (len(cmd) >> 8) & 0xFF
        lsb = (len(cmd)     ) & 0xFF
        checksum = self.zigbeeChecksum(cmd)

        self.write_to_fd(bytearray([ZigbeeProtocol.DELIMITER]) + self.zigbeeEscape([msb, lsb] + list(cmd) + [checksum]))

    def update(self, cur_time_s):
        if not self.is_setup:
            return False

        try:
            if not super(ZigbeeController, self).update(cur_time_s):
                return False

            if not self.process_read_buffer(cur_time_s):
                return False

            to_be_removed = []
            for remote in self.m_remoteZigbees.values():
                if not remote.update(cur_time_s):
                    to_be_removed.append(remote.address16)

            for remote in to_be_removed:
                del self.m_remoteZigbees[remote]
                # delete all outbound and queued messages for that zigbee
                for frameId in list(self.m_outboundMessages.keys()):
                    if self.m_outboundMessages[frameId][0] == remote:
                        del self.m_outboundMessages[frameId]

        except:
            Log.error("", exception=True)

        return True

    def onZigbeeFrame(self, frame, checksum, cur_time_s):
        if self.zigbeeCheckChecksum(frame, checksum):
            cmdID = frame[0]
            if cmdID == 0x8A and len(frame) == 2: # modem status
                pass
            elif cmdID == 0x8B and len(frame) == 7: # Tx status
                frameId = frame[1]
                retryCount = frame[4]
                status = frame[5]
                discoveryStatus = frame[6]
                if status != 0:
                    Log.warning("Failed to send message [{}]: ({} attempts) (status={}) (discovery status={})".format(frameId, retryCount, status, discoveryStatus))
                    if frameId in self.m_outboundMessages:
                        (a, retries, msg) = self.m_outboundMessages[frameId]
                        if retries == 0: # too many retries, stop trying
                            del self.m_outboundMessages[frameId]
                        else:
                            self.m_outboundMessages[frameId] = (a, retries - 1, msg)
                            self.zigbeeAPICall(msg)
                else:
                    if frameId in self.m_outboundMessages:
                        del self.m_outboundMessages[frameId]
                        if len(self.m_queuedMessages) > 0:
                            (addr16, addr64, data) = self.m_queuedMessages[0]
                            self.m_queuedMessages = self.m_queuedMessages[1:]
                            self.zigbeeTx(addr16, addr64, data)

            elif cmdID == 0x90 and len(frame) >= 13: # Rx
                addr64 = 0
                for i in range(1, 9):
                    addr64 |= (frame[i] & 0xFF) << ((8-i) * 8)
                addr16 = ((frame[9] & 0xFF) << 8) | (frame[10] & 0xFF)
                # options = frame[11]
                data = frame[12:]
                if addr16 not in self.m_remoteZigbees:
                    self.addRemote(addr16, addr64)
                if addr16 in self.m_remoteZigbees:
                    self.m_remoteZigbees[addr16].on_read_ready(data, cur_time_s)
            else:
                Log.warning("Unexpected code {}: {}".format(cmdID, list(frame)))
        else:
            Log.warning("Checksum failed!")

    def process_read_buffer(self, cur_time_s):
        # find zigbee frames in self.m_readBuffer and interpret them
        # send zigbee-specific stuff to the respective self.m_remoteZigbees
        while len(self.m_readBuffer) > 0:
            if self.m_readBuffer[0] != 0x7E:
                self.m_readBuffer = self.m_readBuffer[1:]
            else:
                cur_pos = 1

                if cur_pos >= len(self.m_readBuffer):
                    break
                len_msb = self.m_readBuffer[cur_pos]
                cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break
                if len_msb == ZigbeeProtocol.ESCAPE_CHARACTER:
                    len_msb = self.m_readBuffer[cur_pos] ^ ZigbeeProtocol.UNESCAPE_CHARACTER
                    cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break

                len_lsb = self.m_readBuffer[cur_pos]
                cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break
                if len_lsb == ZigbeeProtocol.ESCAPE_CHARACTER:
                    len_lsb = self.m_readBuffer[cur_pos] ^ ZigbeeProtocol.UNESCAPE_CHARACTER
                    cur_pos += 1
                if cur_pos >= len(self.m_readBuffer):
                    break

                content_len = ((len_msb & 0xFF) << 8) | (len_lsb & 0xFF)

                # count escape characters found
                content_and_checksum = bytearray([])
                i = 0
                while i < content_len + 1: # +1 for checksum
                    if cur_pos >= len(self.m_readBuffer):
                        break
                    content_and_checksum.append(self.m_readBuffer[cur_pos])
                    cur_pos += 1
                    if content_and_checksum[-1] == ZigbeeProtocol.ESCAPE_CHARACTER:
                        if cur_pos >= len(self.m_readBuffer):
                            break
                        content_and_checksum[-1] = self.m_readBuffer[cur_pos] ^ ZigbeeProtocol.UNESCAPE_CHARACTER
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
