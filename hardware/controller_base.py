from logs import Log
import serial

#
# A hardware controller is an object that represents a piece of hardware
# (such as an Arduino) connected through a COM port
#
class HardwareController(object):
    # called when the device is detected by the hardware manager
    def __init__(self, hw_manager, comport, baud=9600):
        self.hw_manager = hw_manager
        self.serial_number = comport.serial_number
        try:
            self.serial_port = serial.Serial()
            self.serial_port.baudrate = baud
            self.serial_port.port = comport.device
            self.serial_port.open()
        except Exception as e:
            Log.error("Failed to open serial port for device {} at {}".format(self.serial_number, comport.device))
            self.serial_port = None
            raise e

    # called when the device is detached, before the manager destroys it
    def detach(self):
        try:
            if self.serial_port != None:
                self.serial_port.close()
        except Exception as e:
            Log.warning("Failed to safely close serial port communication for device {}".format(self.serial_number), exception=True)

    # Called to periodically update this device
    # cur_time_s: current time in seconds
    # returns: True to keep the device attached, False to detach it
    def update(self, cur_time_s):
        return True

    # Called when this controller is supposed to set the value of a port
    # port   Port to set
    # value  Value to set the port to
    def set_port_value(self, port, value):
        pass

    # called to identify if any device that this controller controls is in
    # the serial ports
    # ports: list of pyserial COM ports
    # returns: list of serial numbers that this controller should control
    @staticmethod
    def identify(ports):
        return []