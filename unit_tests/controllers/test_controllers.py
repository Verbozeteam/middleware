from config.controllers_config import CONTROLLERS_CONFIG
from config.general_config import GENERAL_CONFIG

from middleware import Core
from things.light import LightSwitch
from controllers.manager import CONTROL_CODES

import pytest
from unittest.mock import Mock
import socket
import select
import struct
import json
import threading
import time
import netifaces
from multiprocessing.pool import ThreadPool

class FakeController(object):
    def __init__(self, socket_connection_manager):
        self.socket = None
        self.buffer = bytearray([])
        self.manager = socket_connection_manager

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
        t = threading.Thread(target=controller_connector, args=(self, ))
        t.start()
        # allow the controllers manager to accept the connection
        for i in range(0, 5):
            time.sleep(0.5)
            self.manager.update(1)
            if len(self.manager.connected_controllers) > 0:
                break
        assert len(self.manager.connected_controllers) > 0
        t.join() # close the thread

    def send_json(self, jobj):
        s = json.dumps(jobj)
        msg = struct.pack("<I", len(s)) + s.encode('utf-8')
        self.socket.send(msg)

    def recv_json(self, maxlen=1024, timeout=1):
        total_time = 0
        while total_time <= timeout:
            if len(self.buffer) >= 4:
                (expected_len, ) = struct.unpack("<I", self.buffer[:4])
                if len(self.buffer) >= 4 + expected_len:
                    ret = json.loads(self.buffer[4:4+expected_len].decode('utf-8'))
                    self.buffer = self.buffer[4+expected_len:]
                    return ret

            self.manager.update(1)

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


class TestSingleController(object):
    def setup(self):
        # initialize the core
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        self.core = Core()
        self.light = list(filter(lambda t: type(t) is LightSwitch, self.core.blueprint.get_things()))[0]

        # allow the controllers manager to actually hosts the server socket
        self.core.ctrl_manager.update(1)

        # connect the fake controller (in a separate thread)
        self.controller = FakeController(self.core.ctrl_manager.socket_connection_manager)
        self.controller.connect()

    # disconnect the fake controller on teardown
    def teardown(self):
        self.controller.disconnect()
        self.core.ctrl_manager.cleanup()

    def test_controller_commands(self):
        # this management command should make make the controller receive the blueprint view
        self.controller.send_json(json.dumps({"code": CONTROL_CODES.GET_BLUEPRINT}))
        expected_result = self.core.blueprint.get_controller_view()
        result = self.controller.recv_json(maxlen=10000, timeout=2)
        assert expected_result == result

        # test non-management commands
        self.light.on_controller_data = Mock()
        self.controller.send_json(json.dumps({"thing": self.light.id, "intensity": 1}))
        time.sleep(0.1)
        self.core.ctrl_manager.update(1)
        self.light.on_controller_data.assert_called_once_with({"intensity": 1})

    def test_hardware_data_to_controller(self):
        self.core.blueprint.broadcast_thing_state(self.light)
        expected_result = {}
        expected_result[self.light.id] = self.light.get_state()
        result = self.controller.recv_json(maxlen=10000, timeout=2)
        assert result == expected_result


class TestMultipleControllers(object):
    NUM_CONTROLLERS = 4

    # make fake controllers on setup
    def setup(self):
        # initialize the core
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        self.core = Core()
        self.light = list(filter(lambda t: type(t) is LightSwitch, self.core.blueprint.get_things()))[0]

        # allow the controllers manager to actually hosts the server socket
        self.core.ctrl_manager.update(1)

        self.controllers = []
        for i in range(self.NUM_CONTROLLERS):
            self.controllers.append(FakeController(self.core.ctrl_manager.socket_connection_manager))
            self.controllers[-1].connect()

    # disconnect the fake controller on teardown
    def teardown(self):
        for C in self.controllers:
            C.disconnect()

        self.core.ctrl_manager.cleanup()

    def test_controller_commands(self):
        # make the first controller send a management command and ONLY IT should get the blueprint view
        self.controllers[0].send_json(json.dumps({"code": CONTROL_CODES.GET_BLUEPRINT}))
        expected_result = self.core.blueprint.get_controller_view()
        result = self.controllers[0].recv_json(maxlen=10000, timeout=2)
        assert expected_result == result

        def asserter(C):
            assert C.recv_json(timeout=0.1) == None
        pool = ThreadPool(9)
        pool.map(lambda C: asserter(C), self.controllers[1:])

    def test_hardware_data_to_controllers(self):
        self.core.blueprint.broadcast_thing_state(self.light)
        expected_result = {}
        expected_result[self.light.id] = self.light.get_state()
        for C in self.controllers:
            assert C.recv_json(maxlen=10000, timeout=2) == expected_result

