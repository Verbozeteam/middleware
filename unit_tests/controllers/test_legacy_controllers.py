from config.general_config import GENERAL_CONFIG
from config.controllers_config import CONTROLLERS_CONFIG

from unit_tests.controllers.test_controllers import FakeController

from middleware import Core

from things.light import LightSwitch, Dimmer
from things.curtain import Curtain
from things.air_conditioner import CentralAC

from unittest.mock import Mock
import time
import select

class FakeLegacyController(FakeController):
    def send_line(self, line):
        self.socket.send(line.encode('utf-8'))

    def recv_data(self, maxlen=1024, timeout=1):
        total_time = 0
        while total_time <= timeout:
            if 254 in self.buffer and 255 in self.buffer:
                i1 = self.buffer.index(254)
                i2 = self.buffer.index(255)
                assert i2 > i1 + 1
                msg = self.buffer[i1+1:i2]
                self.buffer = self.buffer[i2+1:]

                try:
                    num_acs = msg[0]
                    acs = msg[1:1+num_acs*3]
                    acs = [acs[i:i + 3] for i in range(0, len(acs), 3)]
                    num_dimmers  = msg[1+num_acs*3]
                    dimmers      = msg[1+num_acs*3+1:1+num_acs*3+1+num_dimmers]
                    num_switches = msg[1+num_acs*3+1+num_dimmers]
                    switches     = msg[1+num_acs*3+1+num_dimmers+1:1+num_acs*3+1+num_dimmers+1+num_switches]
                    num_curtains = msg[1+num_acs*3+1+num_dimmers+1+num_switches]
                except:
                    assert False

                return {
                    "acs": list(map(lambda ac: {"fan": ac[0], "set_pt": ac[1], "temp": ac[2]}, acs)),
                    "switches": list(switches),
                    "dimmers": list(dimmers),
                    "curtains": [0] * num_curtains,
                }

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


class TestSingleLegacyController(object):
    def setup(self):
        # initialize the core
        CONTROLLERS_CONFIG.LEGACY_MODE = True
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/villa.json"
        self.core = Core()

        self.lights = list(sorted(filter(lambda t: type(t) is LightSwitch, self.core.blueprint.get_things()), key=lambda t: t.id))
        self.dimmers = list(sorted(filter(lambda t: type(t) is Dimmer, self.core.blueprint.get_things()), key=lambda t: t.id))
        self.acs = list(sorted(filter(lambda t: type(t) is CentralAC, self.core.blueprint.get_things()), key=lambda t: t.id))
        self.curtains = list(sorted(filter(lambda t: type(t) is Curtain, self.core.blueprint.get_things()), key=lambda t: t.id))

        # allow the controllers manager to actually hosts the server socket
        self.core.ctrl_manager.update(1)

        # connect the fake controller (in a separate thread)
        self.controller = FakeLegacyController(self.core.ctrl_manager.tcp_socket_connection_manager)
        self.controller.connect()

    # disconnect the fake controller on teardown
    def teardown(self):
        self.controller.disconnect()
        self.core.ctrl_manager.cleanup()

    def test_controller_commands(self):
        #send a bunch of heartbeats
        self.controller.send_line("S\n")
        self.controller.send_line("S\n")
        self.controller.send_line("S\n")

        for thing in self.lights + self.dimmers + self.acs + self.curtains:
            thing.on_controller_data = Mock()

        for i in range(0, len(self.lights)):
            self.controller.send_line("t{}:{}\n".format(len(self.lights) - 1 - i, i % 2))

        for i in range(0, len(self.dimmers)):
            self.controller.send_line("l{}:{}\n".format(i, 10 + i * 10))

        for i in range(0, len(self.curtains)):
            self.controller.send_line("c{}:{}\n".format(i, 2 - i % 3))

        for i in range(0, len(self.acs)):
            self.controller.send_line("a{}:{}\n".format(i, 60)) # 2 * 30.0C
            self.controller.send_line("f{}:{}\n".format(i, 1 - i % 2))

        time.sleep(0.2)
        self.core.ctrl_manager.update(1)
        self.core.ctrl_manager.update(1)

        for i in range(0, len(self.lights)):
            self.lights[i].on_controller_data.assert_called_once_with({"intensity": i % 2})

        for i in range(0, len(self.dimmers)):
            self.dimmers[i].on_controller_data.assert_called_once_with({"intensity": 10 + i * 10})

        for i in range(0, len(self.curtains)):
            self.curtains[i].on_controller_data.assert_called_once_with({"curtain": 2 - i % 3})

        for i in range(0, len(self.acs)):

            for C in self.acs[i].on_controller_data.call_args_list:
                C = C[0][0]
                assert C == {"fan": 1 - i % 2} or abs(C["set_pt"] - 30) < 0.1

    def test_hardware_data_to_controller(self):
        self.controller.send_line("S\n")
        self.controller.send_line("S\n")
        self.controller.send_line("S\n")

        for i in range(0, len(self.lights)):
            self.lights[i].on_controller_data({"intensity": 1 - i % 2})

        for i in range(0, len(self.dimmers)):
            self.dimmers[i].on_controller_data({"intensity": 5 + i * 10})

        for i in range(0, len(self.curtains)):
            self.curtains[i].on_controller_data({"intensity": i % 3})

        for i in range(0, len(self.acs)):
            self.acs[i].current_temperature = 16 # HACK
            self.acs[i].on_controller_data({"set_pt": 20, "fan": 1})

        for thing in self.lights + self.dimmers + self.acs + self.curtains:
            self.core.blueprint.broadcast_thing_state(thing)

        time.sleep(0.2)

        data = self.controller.recv_data(maxlen=10000, timeout=2)
        assert len(data["switches"]) == len(self.lights)
        assert len(data["dimmers"]) == len(self.dimmers)
        assert len(data["acs"]) == len(self.acs)
        assert len(data["curtains"]) == len(self.curtains)

        for i in range(0, len(self.lights)):
            assert data["switches"][len(self.lights)-1-i] == self.lights[i].get_state()["intensity"]

        for i in range(0, len(self.dimmers)):
            assert data["dimmers"][i] == self.dimmers[i].get_state()["intensity"]

        for i in range(0, len(self.acs)):
            assert data["acs"][i]["fan"] == self.acs[i].get_state()["fan"]
            assert abs(data["acs"][i]["set_pt"] / 2 - 20) < 0.1
            assert abs(data["acs"][i]["temp"] - 16) < 0.1

class TestUpgradeDowngrade(object):
    # disconnect the fake controller on teardown
    def teardown(self):
        if hasattr(self, "controller") and self.controller != None:
            self.controller.disconnect()
        self.core.ctrl_manager.cleanup()

    def connect_controller(self, connection_legacy, controller_legacy):
        CONTROLLERS_CONFIG.LEGACY_MODE = connection_legacy

        # initialize the core
        GENERAL_CONFIG.BLUEPRINT_FILENAME = "testing_utils/blueprints/villa.json"
        self.core = Core()

        self.dimmer = list(sorted(filter(lambda t: type(t) is Dimmer, self.core.blueprint.get_things()), key=lambda t: t.id))[0]

        # allow the controllers manager to actually hosts the server socket
        self.core.ctrl_manager.update(1)

        # connect the fake controller (in a separate thread)
        if controller_legacy:
            self.controller = FakeLegacyController(self.core.ctrl_manager.tcp_socket_connection_manager)
        else:
            self.controller = FakeController(self.core.ctrl_manager.tcp_socket_connection_manager)
        self.controller.connect()

    def test_downgrade_simple(self):
        self.connect_controller(connection_legacy=False, controller_legacy=True)

        self.dimmer.on_controller_data = Mock()

        # pretend to be a legacy controller...
        self.controller.send_line("S\n")
        self.controller.send_line("S\n")
        self.controller.send_line("l0:50\n")

        time.sleep(0.2)

        self.core.ctrl_manager.update(1)

        self.dimmer.on_controller_data.assert_called_once_with({"intensity": 50})

    def test_downgrade_complex(self):
        self.connect_controller(connection_legacy=False, controller_legacy=True)

        self.dimmer.on_controller_data = Mock()

        # pretend to be a legacy controller...
        self.controller.send_line("l0:50\n")

        time.sleep(0.2)

        self.core.ctrl_manager.update(1)

        self.dimmer.on_controller_data.assert_called_once_with({"intensity": 50})

    def test_upgrade_simple(self):
        self.connect_controller(connection_legacy=True, controller_legacy=False)

        self.dimmer.on_controller_data = Mock()

        # pretend to be a new controller...
        self.controller.send_json({})
        self.controller.send_json({})
        self.controller.send_json({"thing": self.dimmer.id, "intensity": 50})

        time.sleep(0.2)

        self.core.ctrl_manager.update(1)

        self.dimmer.on_controller_data.assert_called_once_with({"intensity": 50})

    def test_upgrade_complex(self):
        self.connect_controller(connection_legacy=True, controller_legacy=False)

        self.dimmer.on_controller_data = Mock()

        # pretend to be a new controller...
        self.controller.send_json({"thing": self.dimmer.id, "intensity": 50})

        time.sleep(0.2)

        self.core.ctrl_manager.update(1)

        self.dimmer.on_controller_data.assert_called_once_with({"intensity": 50})

