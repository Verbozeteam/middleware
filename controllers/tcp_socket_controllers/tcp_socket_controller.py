from controllers.controller_base import Controller
from logs import Log

from things.air_conditioner import CentralAC
from things.light import LightSwitch, Dimmer
from things.curtain import Curtain
from things.hotel_controls import HotelControls

import struct
import json
import types
import re

#
# A controller connected on the SocketConnectionManager
#
class TCPSocketController(Controller):
    MAXIMUM_COMMAND_LENGTH = 1024 * 32

    def __init__(self, controllers_manager, conn, addr):
        self.connection = conn
        self.address = addr
        self.buffer = bytearray([])
        self.initialize_selectible_fd(conn)
        super(TCPSocketController, self).__init__(controllers_manager, addr[0])

    def __str__(self):
        return str(self.address)

    # Called before the controller gets disconnected
    def destroy_selectible(self):
        super(TCPSocketController, self).destroy_selectible()
        try:
            self.connection.close()
        except: pass

    # Called when the socket has pending bytes to read
    def on_read_ready(self, cur_time_s):
        read = self.connection.recv(1024)
        if not read:
            Log.verboze("Client hung up: {}".format(str(self)))
            return False
        try:
            self.buffer += read
            while len(self.buffer) >= 4:
                command_len = struct.unpack('<I', self.buffer[:4])[0]
                if len(self.buffer) >= 4 + command_len:
                    command = self.buffer[4:4+command_len]
                    self.buffer = self.buffer[4+command_len:]
                    loaded_json = json.loads(command.decode("utf-8"))
                    if type(loaded_json) is str: # ???? (some decoding shit)
                        loaded_json = json.loads(loaded_json)
                    self.on_command(loaded_json)
                elif command_len > self.MAXIMUM_COMMAND_LENGTH:
                    return False
                else:
                    break
            return True
        except:
            Log.warning("TCPSocketController::on_read_ready()", exception=True)
            return False

    # Called when data needs to be sent to the remote controller on the socket
    def send_data(self, json_data, cache=True):
        super(TCPSocketController, self).send_data(json_data, cache)
        try:
            json_data = json.dumps(json_data)
            msg = struct.pack('<I', len(json_data)) + bytearray(json_data.encode("utf-8"))
            self.write_to_fd(msg)
            return True
        except:
            Log.warning("TCPSocketController::send_data({}) Failed".format(str(json_data)), exception=True)
            return False
