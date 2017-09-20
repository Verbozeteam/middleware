from config.hardware_config import HARDWARE_CONFIG
from hardware.arduino_controller import ArduinoController, ArduinoLegacyController
from logs import Log

import time
import serial.tools.list_ports

#
# Hardware manager is responsible for all interaction with hardware
#
class HardwareManager(object):
    def __init__(self, core):
        self.core = core
        # list of (hardware controller type, dictionary) where dictionary
        # is a dictionary mapping a serial number to a HardwareController
        # object
        self.controller_types = {
            "arduino": (ArduinoController, {}),
        }
        if HARDWARE_CONFIG.LEGACY_MODE:
            self.controller_types["arduino"] = (ArduinoLegacyController, {})

        # used for periodic updates
        self.update_timer = 0

    # attaches a device to this manager
    # controller_type: type of the device controller ("arduino", ...)
    # device: a HardwareController device to attach
    def attach_device(self, controller_type, device):
        try:
            self.controller_types[controller_type][1][device.serial_number] = device
            Log.info("Device attached: {}".format(device.serial_number))
        except Exception as e:
            Log.error("Failed to safely attach device {}:".format(device.serial_number), e, exception=True)

    # detaches a device to this manager
    # controller_type: type of the device controller ("arduino", ...)
    # device: a HardwareController device to detach
    def detach_device(self, controller_type, device):
        try:
            device.detach()
        except Exception as e:
            Log.error("Failed to safely detach device {}:".format(device.serial_number), e, exception=True)
        del self.controller_types[controller_type][1][device.serial_number]
        Log.info("Device detached: {}".format(device.serial_number))

    # called to periodically update this manager
    # cur_time_s: current time in seconds
    def update(self, cur_time_s):
        # see if any devices are attached/detached
        if cur_time_s >= self.update_timer:
            try:
                self.update_timer = cur_time_s + HARDWARE_CONFIG.UPDATE_INTERVAL
                com_ports = dict(map(lambda com_port: (com_port.serial_number, com_port), serial.tools.list_ports.comports()))
                for ct_type in self.controller_types.keys():
                    (controller_class, controller_devices) = self.controller_types[ct_type]
                    ct_serials = controller_class.identify(com_ports.values())
                    registered_serials = list(controller_devices.keys())
                    for sn in registered_serials:
                        if sn not in ct_serials:
                            self.detach_device(ct_type, controller_devices[sn])
                    for sn in ct_serials:
                        if sn not in registered_serials:
                            self.attach_device(ct_type, controller_class(self, com_ports[sn]))
            except Exception as e:
                Log.error("Unknown error while identifying COM ports:", e, exception=True)

        # update all currently attached devices
        for ct_type in self.controller_types.keys():
            (controller_class, controller_devices) = self.controller_types[ct_type]
            serials = list(controller_devices.keys())
            for sn in serials:
                device = controller_devices[sn]
                try:
                    keep = device.update(cur_time_s)
                except:
                    keep = False
                if not keep:
                    self.detach_device(ct_type, device)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        # detach all devices
        for ct_Type in self.controller_types.keys():
            (_, controller_devices) = self.controller_types[ct_type]
            for device in controller_devices.values():
                self.detach_device(ct_type, device)

    # Called by a device when it has an updated value on a port
    # device  The HardwareController device that has updated
    # port    The port on which the update happened
    # value   The new value on that port
    def on_port_update(self, device, port, value):
        # @TODO: map local port to global port
        # Forward the update to the core
        self.core.blueprint.on_hardware_data(port, value)

    # Called by the blueprint when hardware is being commanded
    # port   Port being commanded
    # value  Value to set port to
    def on_command(self, port, value):
        # @TODO: map global port to local port (and pick right HW controller)
        for ct_type in self.controller_types.keys():
            (_, controller_devices) = self.controller_types[ct_type]
            if len(controller_devices) > 0:
                controller_devices[list(controller_devices.keys())[0]].set_port_value(port, value)
