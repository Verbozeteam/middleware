from config.controllers_config import CONTROLLERS_CONFIG

import pytest
import socket
import select
import struct
import json
import threading
import time
import netifaces
from multiprocessing.pool import ThreadPool

class FakeController(object):
    def __init__(self, core, tcp_socket_connection_manager):
        self.socket = None
        self.buffer = bytearray([])
        self.core = core
        self.manager = tcp_socket_connection_manager
        self.cache = {} # a cache of everything received so far...

    def connect(self):
        # find hosting IP
        interface = list(self.manager.server_socks.keys())[0]
        ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        port = CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT

        self.disconnect()

        def controller_connector(controller):
            controller.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            controller.socket.connect((ip, port))
            controller.buffer = bytearray([])

        # connect the fake controller (in a separate thread)
        old_num_controllers = len(self.manager.controllers_manager.connected_controllers)
        t = threading.Thread(target=controller_connector, args=(self, ))
        t.start()
        # allow the controllers manager to accept the connection
        for i in range(0, 5):
            time.sleep(0.25)
            self.core.update(1)
            if len(self.manager.controllers_manager.connected_controllers) > old_num_controllers:
                break
        assert len(self.manager.controllers_manager.connected_controllers) > old_num_controllers
        t.join() # close the thread

        # store the object thats in the manager here
        self.connected_controller_object = self.manager.controllers_manager.connected_controllers[-1]

    def send_json(self, jobj):
        s = json.dumps(jobj)
        msg = struct.pack("<I", len(s)) + s.encode('utf-8')
        self.socket.send(msg)
        if "thing" in jobj:
            self.cache[jobj["thing"]] = jobj

    def recv_json(self, maxlen=1024, timeout=1):
        total_time = 0
        while total_time <= timeout:
            if len(self.buffer) >= 4:
                (expected_len, ) = struct.unpack("<I", self.buffer[:4])
                if len(self.buffer) >= 4 + expected_len:
                    ret = json.loads(self.buffer[4:4+expected_len].decode('utf-8'))
                    self.buffer = self.buffer[4+expected_len:]
                    self.cache.update(ret)
                    return ret

            self.core.update(1)

            (ready, _, _) = select.select([self.socket], [], [], 0)
            if ready == [self.socket]:
                b = self.socket.recv(maxlen)
                assert b != None
                self.buffer += b
            else:
                time.sleep(0.1)
                total_time += 0.1

        return None

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
                self.socket = None
            except:
                assert False
        self.core.update(1)
