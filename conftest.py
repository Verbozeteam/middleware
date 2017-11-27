# During testing, use simulation mode for arduino
from config import GENERAL_CONFIG
from logs.log import Log
import sys
GENERAL_CONFIG.SIMULATE_ARDUINO = True
GENERAL_CONFIG.LOG_VERBOZITY = 7
GENERAL_CONFIG.SELECT_TIMEOUT = 0

# content of conftest.py
def pytest_configure(config):
    import sys
    sys._called_from_test = True

    Log.initialize()

def pytest_unconfigure(config):
    import sys  # This was missing from the manual
    del sys._called_from_test
