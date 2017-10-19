# During testing, use simulation mode for arduino
from config import GENERAL_CONFIG
import sys
GENERAL_CONFIG.SIMULATE_ARDUINO = True
GENERAL_CONFIG.LOG_VERBOZITY = 7

# content of conftest.py
def pytest_configure(config):
    import sys
    sys._called_from_test = True

def pytest_unconfigure(config):
    import sys  # This was missing from the manual
    del sys._called_from_test
