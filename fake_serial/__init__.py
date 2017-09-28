from config.general_config import GENERAL_CONFIG

if GENERAL_CONFIG.SIMULATE_ARDUINO:
    from fake_serial.fake_serial import *
else:
    from serial.tools.list_ports import comports
    from serial import Serial