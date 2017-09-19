from controllers.connection_manager import ConnectionManager
from controllers.controller import Controller
from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

import socket
import struct
import json
from select import select

#
# A controller connected on the SocketConnectionManager
#
class SocketController(Controller):
    def __init__(self, connection_manager, conn, addr):
        super(SocketController, self).__init__(connection_manager)
        self.connection = conn
        self.address = addr
        self.buffer = bytearray([])

    def __str__(self):
        return str(self.address)

    # Called before the controller gets disconnected
    def disconnect(self):
        super(SocketController, self).disconnect()
        try:
            self.connection.close()
        except: pass

    # Called when the socket has pending bytes to read
    def on_read_data(self):
        read = self.connection.recv(1024)
        if not read:
            return False
        try:
            self.buffer += read
            if len(self.buffer) >= 4:
                command_len = struct.unpack('i', self.buffer[:4])[0]
                if len(self.buffer) >= 4 + command_len:
                    command = self.buffer[4:4+command_len]
                    self.buffer = self.buffer[4+command_len:]
                    self.on_command(json.loads(command.decode("utf-8")))
            return True
        except Exception as e:
            return False

    # Called when data needs to be sent to the remote controller on the socket
    def on_send_data(self, json_data):
        try:
            json_data = json.dumps(json_data)
            msg = struct.pack('i', len(json_data)) + bytearray(json_data.encode("utf-8"))
            self.connection.send(msg)
            return True
        except:
            return False

#
# A socketIO-based connection manager for controllers
#
class SocketConnectionManager(ConnectionManager):
    def __init__(self, controllers_manager):
        super(SocketConnectionManager, self).__init__(controllers_manager)
        self.server_sock = None
        self.reconnect_timer = 0
        self.reset_connection()

    # Resets the server socket
    def reset_connection(self):
        self.cleanup()
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind((CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_IP, CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT))
            self.server_sock.listen(CONTROLLERS_CONFIG.SOCKET_SERVER_MAX_CONNECTIONS)
        except Exception as e:
            Log.error(str(e), exception=True)
            try:
                self.server_sock.close()
            except: pass
            self.server_sock = None

    # non-blocking listening to new connections and connected controllers
    def update(self, cur_time_s):
        if not self.server_sock:
            if cur_time_s >= self.reconnect_timer:
                self.reset_connection()
                self.reconnect_timer = cur_time_s + CONTROLLERS_CONFIG.SOCKET_SERVER_RECONNECT_TIMEOUT
            if not self.server_sock:
                return

        controllers_descriptors = list(map(lambda c: c.connection, self.connected_controllers))
        try:
            (ready_descriptors, _, _) = select([self.server_sock] + controllers_descriptors, [], [], 0)
            for desc in ready_descriptors:
                if desc == self.server_sock:
                    conn, addr = self.server_sock.accept()
                    self.register_controller(SocketController(self, conn, addr))
                else:
                    for c in self.connected_controllers:
                        if c.connection == desc:
                            try:
                                if not c.on_read_data():
                                    self.disconnect_controller(c)
                            except Exception as e:
                                self.disconnect_controller(c)
        except Exception as e:
            Log.error(str(e), exception=True)
            self.cleanup()
        super(SocketConnectionManager, self).update(cur_time_s)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        super(SocketConnectionManager, self).cleanup()
        try:
            self.server_sock.close()
        except: pass
        self.server_sock = None
