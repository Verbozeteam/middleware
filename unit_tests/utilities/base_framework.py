from config.hardware_config import HARDWARE_CONFIG
from core.core import Core

import time

class BaseTestFramework(object):
    current_fake_time = 0
    extra_update_calls = [] # Functions that will be called every update
    LEGACY_MODE = False

    def setup(self):
        # Setup the system
        HARDWARE_CONFIG.LEGACY_MODE = self.LEGACY_MODE
        self.core = Core()
        self.extra_update_calls = [self.core.update]

    def teardown(self):
        self.core.cleanup()
        self.core = None

    def wait_for_condition(self, condition, attempts=100):
        count = 0
        while True:
            self.step_time()
            try:
                if condition(self):
                    return True
            except: pass
            time.sleep(0.02)
            count += 1
            if count == attempts:
                assert condition(self)

    def step_time(self):
        self.current_fake_time += 0.1
        for f in self.extra_update_calls:
            f(self.current_fake_time)
