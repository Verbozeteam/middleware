from unit_tests.utilities.base_framework import BaseTestFramework
from config.controllers_config import CONTROLLERS_CONFIG
from config.general_config import GENERAL_CONFIG

from core.core import Core
from things.light import LightSwitch
from controllers.manager import CONTROL_CODES

import pytest
from unittest.mock import Mock, call
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

class TestSingleController(BaseTestFramework):
    def setup(self):
        # initialize the core
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/lights.json"
        CONTROLLERS_CONFIG.LEGACY_MODE = False

        super(TestSingleController, self).setup()

        self.light = list(filter(lambda t: type(t) is LightSwitch, self.core.blueprint.get_things()))[0]

        # allow the controllers manager to actually hosts the server socket
        self.core.update(1)

        # connect the fake controller (in a separate thread)
        self.controller = FakeController(self.core, self.core.ctrl_manager.tcp_socket_connection_manager)
        self.controller.connect()

    # disconnect the fake controller on teardown
    def teardown(self):
        self.controller.disconnect()
        super(TestSingleController, self).teardown()

    def test_controller_commands(self):
        # this management command should make make the controller receive the blueprint view
        self.controller.send_json(json.dumps({"code": CONTROL_CODES.GET_BLUEPRINT}))
        expected_result = self.core.blueprint.get_controller_view()

        cur_view = {}
        def received_view(self):
            cur_view.update(self.controller.recv_json(maxlen=10000, timeout=2))
            for key in expected_result:
                if key not in cur_view or cur_view[key] != expected_result[key]:
                    return False
            return True

        self.wait_for_condition(received_view)

        # test non-management commands
        self.light.set_state = Mock()
        self.controller.send_json(json.dumps({"thing": self.light.id, "intensity": 1}))

        def controller_recevied(self):
            return call({"thing": self.light.id, "intensity": 1}) in self.light.set_state.mock_calls

        self.wait_for_condition(controller_recevied)

    def test_hardware_data_to_controller(self):
        for i in range(0, 2):
            self.light.set_state({"intensity": i})
            expected_result = {
                self.light.id: self.light.get_state()
            }

            cur_view = {}
            def received_view(self):
                cur_view.update(self.controller.recv_json(maxlen=10000, timeout=2))
                for key in expected_result:
                    if key not in cur_view or cur_view[key] != expected_result[key]:
                        return False
                return True

            self.wait_for_condition(received_view)
