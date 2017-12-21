from unit_tests.utilities.base_framework import BaseTestFramework
from unit_tests.utilities.fake_controller import FakeController
from config.controllers_config import CONTROLLERS_CONFIG
from config.general_config import GENERAL_CONFIG

from core.core import Core
from things.light import LightSwitch
from controllers.manager import CONTROL_CODES

from unittest.mock import Mock, call



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
        self.controller.send_json({"code": CONTROL_CODES.GET_BLUEPRINT})
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
        self.controller.send_json({"thing": self.light.id, "intensity": 1})

        def controller_recevied(self):
            return call({"thing": self.light.id, "intensity": 1}, token_from="") in self.light.set_state.mock_calls

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
                    if key not in cur_view:
                        return False
                    for subkey in expected_result[key]:
                        if subkey not in cur_view[key] or cur_view[key][subkey] != expected_result[key][subkey]:
                            return False
                return True

            self.wait_for_condition(received_view)
