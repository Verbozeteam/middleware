
#
# A hardware controller is an object that represents a piece of hardware
# (such as an Arduino) connected through a COM port
#
class HardwareController(object):
    # called when the device is detected by the hardware manager
    def __init__(self, comport):
        self.serial_number = comport.serial_number

    # called when the device is detached, before the manager destroys it
    def detach(self):
        pass

    # called to identify if any device that this controller controls is in
    # the serial ports
    # ports: list of pyserial COM ports
    # returns: list of serial numbers that this controller should control
    @staticmethod
    def identify(ports):
        return []