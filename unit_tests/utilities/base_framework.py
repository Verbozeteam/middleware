from config.hardware_config import HARDWARE_CONFIG
from core.core import Core

import time

class BaseTestFramework(object):
    current_fake_time = 0
    LEGACY_MODE = False

    def setup(self):
        # Setup the system
        HARDWARE_CONFIG.LEGACY_MODE = self.LEGACY_MODE
        self.core = Core()

    def teardown(self):
        self.core.cleanup()
        self.core = None

    def wait_for_condition(self, condition, attempts=100):
        count = 0
        while True:
            self.current_fake_time += 0.1
            self.core.update(self.current_fake_time)
            if condition(self):
                return True
            time.sleep(0.02)
            count += 1
            if count == attempts:
                assert condition(self)