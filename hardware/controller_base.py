from logs import Log
import fake_serial

from core.select_service import Selectible

#
# A hardware controller is an object that represents a piece of hardware
# (such as an Arduino) connected through a COM port
#
class HardwareController(Selectible):
    # called when the device is detected by the hardware manager
    def __init__(self, hw_manager, comport, baud=9600, fake_serial_port=None):
        self.hw_manager = hw_manager
        self.serial_number = comport.serial_number
        try:
            self.serial_port = fake_serial.Serial()
            if fake_serial_port:
                self.serial_port.socket_port = fake_serial_port
            self.serial_port.baudrate = baud
            self.serial_port.port = comport.device
            self.serial_port.open()
            self.cache = {} # cache of port -> output
        except Exception as e:
            Log.error("Failed to open serial port for device {} at {}".format(self.serial_number, comport.device))
            self.serial_port = None
            raise e

        self.initialize_selectible_fd(self.serial_port)

        self.hw_manager.register_controller(self)

        Log.info("Device attached: {}".format(self.serial_number))

    # Clears the cache on this device
    def clear_cache(self):
        self.cache = {}

    # called when the device is detached, before the manager destroys it
    def destroy_selectible(self):
        super(HardwareController, self).destroy_selectible()
        try:
            if self.serial_port != None:
                self.serial_port.close()
        except:
            Log.warning("Failed to safely close serial port communication for device {}".format(self.serial_number), exception=True)

        self.hw_manager.deregister_controller(self)

        Log.info("Device detached: {}".format(self.serial_number))

    # Called to periodically update this device
    # cur_time_s current time in seconds
    # returns True to keep the device attached, False to detach it
    def update(self, cur_time_s):
        try:
            all_things = self.hw_manager.core.blueprint.get_things()

            for thing in all_things:
                state = thing.get_hardware_state()
                for port in state.keys():
                    if port not in self.cache or state[port] != self.cache[port]:
                        self.set_port_value(port, state[port])
        except:
            Log.error("HardwareController::update() Failed", exception=True)
            return False
        return True

    # whether or not the controller is synced and functional
    def is_synced(self):
        return True

    # Sends a command to the controller to set a port to a certain output value
    def set_port_value(self, port, value):
        Log.hammoud("HardwareController::set_port_value({}, {})".format(port, value))
        self.cache[port] = value

    # called to identify if any device that this controller controls is in
    # the serial ports
    # ports  list of pyserial COM ports
    # returns list of serial numbers that this controller should control
    @staticmethod
    def identify(ports):
        return []