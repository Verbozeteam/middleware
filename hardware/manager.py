from config.hardware_config import HARDWARE_CONFIG
from hardware.arduino_controller import ArduinoController, ArduinoLegacyController
from hardware.zigbee_controller import ZigbeeController
from logs import Log

import time
import fake_serial

#
# Hardware manager is responsible for all interaction with hardware
#
class HardwareManager(object):
    def __init__(self, core):
        self.core = core
        self.connected_controllers = {} # dictionary of serial number -> hardware controller
        self.controller_types = [] if HARDWARE_CONFIG.DISABLE_HARDWARE else [
            ArduinoLegacyController if HARDWARE_CONFIG.LEGACY_MODE else ArduinoController,
            ZigbeeController,
        ]

        self.update_timer = 0 # used for periodic updates

    def register_controller(self, controller):
        self.connected_controllers[controller.serial_number] = controller

    def deregister_controller(self, controller):
        try:
            del self.connected_controllers[controller.serial_number]
        except: pass

    def update_com_ports(self, cur_time_s):
        if cur_time_s >= self.update_timer: # check if any devices are attached/detached
            try:
                self.update_timer = cur_time_s + HARDWARE_CONFIG.UPDATE_INTERVAL
                com_ports = dict(map(lambda com_port: (com_port.serial_number, com_port), fake_serial.comports()))
                registered_serials = list(self.connected_controllers.keys())
                all_identified_serials = []
                for controller_type in self.controller_types:
                    identified_serials = controller_type.identify(com_ports.values())
                    all_identified_serials += identified_serials
                    for serial in identified_serials:
                        if serial not in registered_serials:
                            controller_type(self, com_ports[serial]) # create a controller (will register itself)
                for serial in registered_serials:
                    if serial not in all_identified_serials:
                        self.connected_controllers[serial].destroy_selectible()
            except:
                Log.error("Unknown error while identifying COM ports", exception=True)

    # called to periodically update this manager
    # cur_time_s: current time in seconds
    def update(self, cur_time_s):
        self.update_com_ports(cur_time_s)

        for controller in list(self.connected_controllers.values()):
            try:
                keep = controller.update(cur_time_s)
            except:
                keep = False
            if not keep:
                controller.destroy_selectible()

    # Called when this manager needs to free all its resources
    def cleanup(self):
        # detach all devices
        for controller in list(self.connected_controllers.values()):
            controller.destroy_selectible()

    # Called by a device when it has an updated value on a port
    # device  The HardwareController device that has updated
    # port    The port on which the update happened
    # value   The new value on that port
    def on_port_update(self, device, port, value):
        # @TODO: map local port to global port
        # Forward the update to the respective thing
        try:
            things = self.core.blueprint.get_listening_things_by_port(port)
            for thing in things:
                thing.set_hardware_state(port, value)
        except:
            Log.error("HardwareManager::on_port_update({}, {}, {})".format(device, port, value), exception=True)
