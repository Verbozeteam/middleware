from hardware.controller_base import HardwareController
from logs import Log

import struct

class MESSAGE_TYPE:
    SYNC_SEQUENCE                   = 254

    FROMDEVICE_PINSTATE             = 0

    TODEVICE_SET_PIN_MODE           = 1
    TODEVICE_SET_VIRTUAL_PIN_MODE   = 2
    TODEVICE_SET_PIN_OUTPUT         = 3
    TODEVICE_READ_PIN_INPUT         = 4
    TODEVICE_REGISTED_PIN_LISTENER  = 5
    TODEVICE_RESET_BOARD            = 6

class PIN_TYPE:
    UNKNOWN = (-1, "")
    DIGITAL = (0, "d")
    ANALOG  = (1, "a")
    VIRTUAL = (2, "v")

    @staticmethod
    def from_id(id):
        for attr in dir(PIN_TYPE):
            attr = getattr(PIN_TYPE, attr)
            if type(attr) == type(()) and len(attr) == 2 and attr[0] == id:
                return attr
        return (-1, "")

    @staticmethod
    def from_str(ch):
        for attr in dir(PIN_TYPE):
            attr = getattr(PIN_TYPE, attr)
            if type(attr) == type(()) and len(attr) == 2 and attr[1] == ch:
                return attr
        return (-1, "")

class PIN_MODE:
    INPUT        = 0
    OUTPUT       = 1
    PWM          = 2
    INPUT_PULLUP = 3

class VIRTUAL_PIN_TYPE:
    CENTRAL_AC    = 0
    ISR_LIGHT     = 1
    ISR_LIGHT2    = 2
    MULTIPLEX_PIN = 3

class ArduinoProtocol:
    # 8-byte sequence that represents a sequence sent periodically by the Arduino
    # to sync the communication
    FULL_SYNC_SEQUENCE = bytearray([254, 6, 253, 11, 76, 250, 250, 255])
    SYNC_SEQUENCE = bytearray([254, 6, 252, 11, 76, 250, 250, 255])

    VALID_MESSAGE_TYPES = list(map(lambda attr: getattr(MESSAGE_TYPE, attr), filter(lambda di: type(getattr(MESSAGE_TYPE, di)) == type(0), dir(MESSAGE_TYPE))))
    MAX_MESSAGE_LEN = 20 # max length of a legit message. best value should be as tight as possible

    pin_offsets = {0: 0, 1: 0, 2: 0} # offset of pins (digital, analog, virtual)
    pin_ranges = {0: -1, 1: -1, 2: -1} # maximum pin index allowed (-1 for no maximum)

    @staticmethod
    def set_pin_ranges(digital, num_digital, analog, num_analog, virtual, num_virtual):
        ArduinoProtocol.pin_offsets = {0: digital, 1: analog, 2: virtual}
        ArduinoProtocol.pin_ranges = {0: num_digital, 1: num_analog, 2: num_virtual}

    @staticmethod
    def on_message(controller, message_type, message):
        Log.hammoud("ArduinoProtocol::on_message({}, {} --{} bytes--)".format(message_type, list(message), len(message)))
        if message_type == MESSAGE_TYPE.FROMDEVICE_PINSTATE:
            # expected message: bytearray([port_type, port_number, value])
            if len(message) != 3:
                return False
            (port_type, port_number, value) = message
            port_type = PIN_TYPE.from_id(port_type)[1]
            controller.hw_manager.on_port_update(controller, port_type+str(port_number), value)
        else:
            return False
        return True

    @staticmethod
    def create_set_pin_mode(pin, mode):
        pin_type = PIN_TYPE.from_str(pin[0])[0]
        pin_index = int(pin[1:]) + ArduinoProtocol.pin_offsets[pin_type]
        if pin_index < 0 or (pin_index >= ArduinoProtocol.pin_ranges[pin_type] and ArduinoProtocol.pin_ranges[pin_type] != -1):
            return bytearray([])
        return struct.pack('BBBBB', 1, 3, pin_type, pin_index, mode)

    @staticmethod
    def create_set_virtual_pin_mode(pin, data):
        pin_type = PIN_TYPE.from_str(pin[0])[0]
        pin_index = int(pin[1:]) + ArduinoProtocol.pin_offsets[pin_type]
        if pin_index < 0 or (pin_index >= ArduinoProtocol.pin_ranges[pin_type] and ArduinoProtocol.pin_ranges[pin_type] != -1):
            return bytearray([])
        return struct.pack('BBBB', 2, len(data)+2, 2, pin_index) + bytearray(data)

    @staticmethod
    def create_set_pin_output(pin, output):
        pin_type = PIN_TYPE.from_str(pin[0])[0]
        pin_index = int(pin[1:]) + ArduinoProtocol.pin_offsets[pin_type]
        if pin_index < 0 or (pin_index >= ArduinoProtocol.pin_ranges[pin_type] and ArduinoProtocol.pin_ranges[pin_type] != -1):
            return bytearray([])
        return struct.pack('BBBBB', 3, 3, pin_type, pin_index, output)

    @staticmethod
    def create_read_pin_input(pin):
        pin_type = PIN_TYPE.from_str(pin[0])[0]
        pin_index = int(pin[1:]) + ArduinoProtocol.pin_offsets[pin_type]
        if pin_index < 0 or (pin_index >= ArduinoProtocol.pin_ranges[pin_type] and ArduinoProtocol.pin_ranges[pin_type] != -1):
            return bytearray([])
        return struct.pack('BBBBB', 4, 2, pin_type, pin_index)

    @staticmethod
    def create_register_pin_listener(pin, interval_ms):
        pin_type = PIN_TYPE.from_str(pin[0])[0]
        pin_index = int(pin[1:]) + ArduinoProtocol.pin_offsets[pin_type]
        if pin_index < 0 or (pin_index >= ArduinoProtocol.pin_ranges[pin_type] and ArduinoProtocol.pin_ranges[pin_type] != -1):
            return bytearray([])
        return struct.pack('<BBBBI', 5, 6, pin_type, pin_index, interval_ms)

    @staticmethod
    def create_reset_board():
        return struct.pack('BB', 6, 0)

#
# An Arduino controller
#
class ArduinoController(HardwareController):
    def __init__(self, hw_manager, comport, fake_serial_port=None):
        self.read_buffer = bytearray([])
        self.half_sync = False
        self.full_sync = False
        self.sync_send_timer = 0
        self.sync_send_period = 1
        self.receive_timeout = -1
        self.is_initialized = False
        super(ArduinoController, self).__init__(hw_manager, comport, baud=9600, fake_serial_port=fake_serial_port)

    # Initializes the Things that this controller controls
    def initialize_board(self):
        Log.hammoud("ArduinoController::initialize_board()")
        try:
            self.write_to_fd(ArduinoProtocol.create_reset_board())
            things = self.hw_manager.core.blueprint.get_things()
            for thing in things:
                all_ports = list(thing.input_ports.keys()) + list(thing.output_ports.keys())
                virtual_ports = []
                for p in all_ports:
                    if "v" in p:
                        virtual_ports.append(p)
                virtual_ports = sorted(virtual_ports, key=lambda p: int(p[1:]))
                if len(virtual_ports) > 0 and (("virtual_port_data" not in dir(thing)) or (len(virtual_ports) != len(thing.virtual_port_data))):
                    Log.error("Thing {} has a virtual port but no virtual_port_data".format(thing.id))
                    continue

                for i in range(0, len(virtual_ports)):
                    self.write_to_fd(ArduinoProtocol.create_set_virtual_pin_mode(virtual_ports[i], thing.virtual_port_data[i]))

                for port in thing.input_ports.keys():
                    read_interval = thing.input_ports[port]
                    pin_mode = PIN_MODE.INPUT
                    if type(read_interval) is not int:
                        read_interval = thing.input_ports[port]["read_interval"]
                        pin_mode = PIN_MODE.INPUT_PULLUP if thing.input_ports[port].get("is_pullup", False) else PIN_MODE.INPUT
                    if port not in virtual_ports:
                        self.write_to_fd(ArduinoProtocol.create_set_pin_mode(port, pin_mode))
                    self.write_to_fd(ArduinoProtocol.create_register_pin_listener(port, read_interval))

                for port in thing.output_ports.keys():
                    if port not in virtual_ports:
                        self.write_to_fd(ArduinoProtocol.create_set_pin_mode(port, thing.output_ports[port]))
        except:
            Log.fatal("Failed to initalize board!", exception=True)
        self.clear_cache() # clear cache so things can be written to the board
        self.is_initialized = True

    # Checks or sets the sync state with the controller
    # set_to   If not None, sets the sync state to to this
    # returns  The sync state
    def is_in_sync(self, set_to=None):
        if set_to != None:
            self.half_sync = set_to
            self.full_sync = set_to
            if set_to == False:
                self.read_buffer = bytearray([]) # no sync -> empty read buffer
                self.sync_send_timer = 0
                self.sync_send_period = 1
                self.is_initialized = False
            elif set_to == True:
                self.sync_send_period = 10

        return self.full_sync

    # Synchronizes the read buffer with the Arduino if its not already in sync.
    # returns True if the buffer is in sync, False otherwise
    def sync_input_buffer(self, cur_time_s):
        if cur_time_s >= self.sync_send_timer:
            self.sync_send_timer = cur_time_s + self.sync_send_period
            self.write_to_fd(ArduinoProtocol.FULL_SYNC_SEQUENCE if self.half_sync else ArduinoProtocol.SYNC_SEQUENCE)
            Log.hammoud("ArduinoController::sync_input_buffer() wrote a sync sequence {}".format("full" if self.full_sync else ("half" if self.half_sync else "NO SYNC")))

        while not self.full_sync and len(self.read_buffer) >= len(ArduinoProtocol.SYNC_SEQUENCE):
            found_sync = False
            for sync_start in range(0, len(self.read_buffer) - len(ArduinoProtocol.SYNC_SEQUENCE) + 1):
                is_sync_start = True # Whether sync_start is where a sync sequence starts
                for sync_index in range(len(ArduinoProtocol.SYNC_SEQUENCE)):
                    if self.read_buffer[sync_start+sync_index] != ArduinoProtocol.SYNC_SEQUENCE[sync_index] and self.read_buffer[sync_start+sync_index] != ArduinoProtocol.FULL_SYNC_SEQUENCE[sync_index]:
                        is_sync_start = False # Not the right sequence
                        break
                if is_sync_start:
                    found_sync = True
                    break

            if found_sync:
                found_full = (self.read_buffer[sync_start:sync_start+len(ArduinoProtocol.SYNC_SEQUENCE)]) == ArduinoProtocol.FULL_SYNC_SEQUENCE
                self.read_buffer = self.read_buffer[sync_start+len(ArduinoProtocol.SYNC_SEQUENCE):]
                if found_full:
                    Log.hammoud("ArduinoController::sync_input_buffer() found FULL sequence")
                    self.is_in_sync(True)
                    self.sync_send_timer = 0
                else:
                    Log.hammoud("ArduinoController::sync_input_buffer() found HALF sequence")
                    self.half_sync = True
            else:
                truncate_size = 0
                for truncate_size in range(0, len(self.read_buffer)):
                    if self.read_buffer[truncate_size] == ArduinoProtocol.SYNC_SEQUENCE[0]:
                        break
                # truncate the beginning of the read buffer
                self.read_buffer = self.read_buffer[truncate_size:]

        if self.full_sync and not self.is_initialized:
            self.initialize_board()

        return self.is_in_sync()

    # Parse the read buffer's messages and interpret them. If any message
    # corruption is detected, it will set wait_for_sync to True.
    # returns True if the connection should continue, False otherwise
    def process_read_buffer(self):
        while len(self.read_buffer) > 2:
            (msg_type, msg_len) = struct.unpack('BB', self.read_buffer[:2])
            if len(self.read_buffer) >= 2 + msg_len:
                msg = self.read_buffer[2:2+msg_len]
                self.read_buffer = self.read_buffer[2+msg_len:]
                if not self.on_message(msg_type, msg):
                    # Failed to understand the message, need to sync again
                    Log.error("ArduinoController:process_read_buffer() read wrong message (type={}, length={}): {}".format(msg_type, msg_len, msg))
                    self.is_in_sync(False)
                    break
            elif msg_len > ArduinoProtocol.MAX_MESSAGE_LEN or msg_type not in ArduinoProtocol.VALID_MESSAGE_TYPES:
                Log.error("ArduinoController:process_read_buffer() wrong message type ({}) or length ({}). Read buffer: {}".format(msg_type, msg_len, str(list(self.read_buffer))))
                self.is_in_sync(False)
            else:
                break
        return True

    # Called when a message has been found on the read buffer.
    # message_type Message type
    # message      The contents of the message
    # returns      True if the message is valid, False otherwise
    def on_message(self, message_type, message):
        if message_type == MESSAGE_TYPE.SYNC_SEQUENCE: # This message is just a SYNC sequence
            return message == ArduinoProtocol.FULL_SYNC_SEQUENCE[2:]
        return ArduinoProtocol.on_message(self, message_type, message)

    def update(self, cur_time_s):
        if not super(ArduinoController, self).update(cur_time_s):
            return False

        if self.receive_timeout < 0:
            self.receive_timeout = cur_time_s + 13

        if cur_time_s > self.receive_timeout:
            Log.warning("ArduinoController::update() timed out")
            return False # haven't received anything in a long time!

        if self.sync_input_buffer(cur_time_s):
            return self.process_read_buffer()

        return True

    def set_port_value(self, port, value):
        super(ArduinoController, self).set_port_value(port, value)
        if self.is_in_sync():
            self.write_to_fd(ArduinoProtocol.create_set_pin_output(port, value))

    def on_read_ready(self, cur_time_s):
        try:
            b = self.serial_port.read(self.serial_port.in_waiting)
            self.read_buffer += b
            self.receive_timeout = cur_time_s + 13
        except:
            Log.error("ArduinoController::on_read_ready() failed", exception=True)
            return False
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
                    break
        return ret

#
# A legacy Arduino controller that uses the old protocol for communication
#
class ArduinoLegacyController(ArduinoController):

    # Legacy Arduino pin layout
    # curtains   : 22+ (UP, DOWN, UP, DOWN, ...)
    # onoff      : 37-
    # fans       : 48-49
    # ACs        : 50-51
    # temp sensor: 53
    # dimmers    : 4-7 (analog PWM output)
    # central ACs: 8-9 (analog PWM output)
    # SYNC       : digital 3
    # hotel card : 44 (input 0v/5v)
    # hotel power: 42 (output 0v/5v)

    def __init__(self, hw_manager, comport):
        self.read_buffer = bytearray([])
        self.BEGINNING_BYTE = 254
        self.ENDING_BYTE = 255
        super(ArduinoLegacyController, self).__init__(hw_manager, comport, fake_serial_port=9912)

    def is_in_sync(self, set_to=None):
        return True

    # Syncing the controller is handled while reading the buffer
    def sync_input_buffer(self, cur_time_s):
        return True

    # Parse the read buffer's messages and interpret them. If any message
    # corruption is detected, it will discard the message(s) until a new
    # beginning is detected
    # returns True if the connection should continue, False otherwise
    def process_read_buffer(self):
        while True:
            try:
                beg_idx = self.read_buffer.index(bytearray([self.BEGINNING_BYTE]))
            except:
                break
            self.read_buffer = self.read_buffer[beg_idx:]
            try:
                end_idx = self.read_buffer.index(bytearray([self.ENDING_BYTE]))
            except:
                break
            msg = self.read_buffer[beg_idx+1:end_idx]
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
            for ac in range(num_acs):
                ACs.append((message[base_idx+0*num_acs+ac], message[base_idx+1*num_acs+ac], message[base_idx+2*num_acs+ac]))
            base_idx += 3*num_acs
            num_dimmers = message[base_idx]
            base_idx += 1
            dimmers = list(message[base_idx:base_idx+num_dimmers])
            base_idx += num_dimmers
            num_lights = message[base_idx]
            base_idx += 1
            lights = list(message[base_idx:base_idx+num_lights])
            base_idx += num_lights
            # num_curtains = message[base_idx]
            base_idx += 1
            if base_idx != len(message):
                raise Exception(1) # invalid message...
            for i in range(len(ACs)):
                ArduinoProtocol.on_message(self, MESSAGE_TYPE.FROMDEVICE_PINSTATE, bytearray([PIN_TYPE.DIGITAL[0], 48+i, ACs[i][0]]))
                ArduinoProtocol.on_message(self, MESSAGE_TYPE.FROMDEVICE_PINSTATE, bytearray([PIN_TYPE.VIRTUAL[0], i, ACs[i][2]]))
            for i in range(len(dimmers)):
                ArduinoProtocol.on_message(self, MESSAGE_TYPE.FROMDEVICE_PINSTATE, bytearray([PIN_TYPE.DIGITAL[0], 4+i, dimmers[i]]))
            for i in range(len(lights)):
                ArduinoProtocol.on_message(self, MESSAGE_TYPE.FROMDEVICE_PINSTATE, bytearray([PIN_TYPE.DIGITAL[0], 37-i, lights[i]]))
            return True
        except:
            Log.error("ArduinoLegacyController::on_message() Failed", exception=True)
            return False

    def set_port_value(self, port, value):
        super(ArduinoLegacyController, self).set_port_value(port, value)
        try:
            port_type = port[0]
            port = int(port[1:])
            if port_type == "v" and port == 0: # AC set point
                self.write_to_fd("a{}:{}\n".format(port, int(value*2)).encode('utf-8'))
            if port >= 22 and port <= 27: # curtain
                curtain = int((port - 22) / 2)
                value = 0 if value == 0 else (1 if port % 2 == 0 else 2)
                self.write_to_fd("c{}:{}\n".format(curtain, value).encode('utf-8'))
            elif port >= 28 and port <= 37: # switch
                self.write_to_fd("t{}:{}\n".format(37 - port, value).encode('utf-8'))
            elif port >= 4 and port <= 7: # dimmer
                self.write_to_fd("l{}:{}\n".format(port - 4, int(float(value)/2.55)).encode('utf-8'))
            elif port >= 8 and port <= 9: # central AC
                self.write_to_fd("a{}:{}\n".format(port - 8, value).encode('utf-8'))
            elif port >= 48 and port <= 49:
                self.write_to_fd("f{}:{}\n".format(port - 48, value).encode('utf-8'))
        except:
            pass

