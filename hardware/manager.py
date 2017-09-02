from config.hardware_config import HARDWARE_CONFIG
from hardware.arduino_controller import ArduinoController
from logs import Log

import time
import serial.tools.list_ports

#
# Hardware manager is responsible for all interaction with hardware
# 
class HardwareManager(object):
    def __init__(self):
        # list of (hardware controller type, dictionary) where dictionary
        # is a dictionary mapping a serial number to a controller_base
        # object
        self.controller_types = [
            (ArduinoController, {})
        ]
        # used for periodic updates
        self.update_timer = 0

    def update(self, cur_time_s):
        if cur_time_s >= self.update_timer:
            self.update_timer = cur_time_s + HARDWARE_CONFIG.UPDATE_INTERVAL
            com_ports = dict(map(lambda com_port: (com_port.serial_number, com_port), serial.tools.list_ports.comports()))
            for ct in self.controller_types:
                ct_serials = ct[0].identify(com_ports.values())
                registered_serials = list(ct[1].keys())
                for s in registered_serials:
                    if s not in ct_serials:
                        Log.info("Device detached: {}".format(s))
                        ct[1][s].detach()
                        del ct[1][s]
                for s in ct_serials:
                    if s not in registered_serials:
                        Log.info("Device detected: {}".format(s))
                        ct[1][s] = ct[0](com_ports[s])



