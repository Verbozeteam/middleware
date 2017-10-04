from config.controllers_config import CONTROLLERS_CONFIG
from config.general_config import GENERAL_CONFIG

from middleware import Core

import socket
import select
import json

class FakeController(object):
    def __init__(self):
        self.socket = None
        self.buffer = bytearray([])

    def connect(self, ip, port):
        self.disconnect()
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            self.buffer = bytearray([])
        except:
            assert False

    def send_json(self, jobj):
        s = json.dumps(jobj)
        msg = struct.pack("<I", len(s)) + bytearray(s)
        self.socket.send(msg)

    def recv_json(self, maxlen=1024, timeout=1):
        while True:
            if len(self.buffer) >= 4:
                expected_len = struct.unpack("<I", self.buffer[:4])
                if len(self.buffer) >= 4 + expected_len:
                    ret = json.loads(self.buffer[4:4+expected_len].decode('utf-8'))
                    self.buffer = self.buffer[4+expected_len:]
                    return ret

            (ready, _, _) = select.select([self.socket], [], [], timeout)
            assert ready == [self.socket]
            b = self.socket.recv(maxlen)
            assert b > 0
            self.buffer += b

    def disconnect(self):
        if self.socket:
            try:
                self.socket.disconnect()
                self.socket = None
            except:
                assert False

# @pytest.fixture(scope="module")
# def configure_controller():
#     self.core = Core()
#     self.core.ctrl_manager.update(1)
#     self.controller = FakeController()
#     self.controller.connect("192.168.10.14", CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT)
#     self.core.ctrl_manager.update(2)
#     assert len(self.socket_connection_manager.connected_controllers) == 1

#     yield configure_controller

#     self.controller.disconnect()
#     self.core.update(10000000)
#     assert len(self.socket_connection_manager.connected_controllers) == 0


# class TestController(object):
#     def setup(self):
#         pass

#     def test_ass(self):
#         print ("hello")
