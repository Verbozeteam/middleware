from controllers.controller_base import Controller
from logs import Log

from things.air_conditioner import CentralAC
from things.light import LightSwitch, Dimmer
from things.curtain import Curtain
from things.hotel_controls import HotelControls

import struct
import json
import types
import re

# Makes a TCPSocketLegacyController behave like a non-legacy controller
# controller  A TCPSocketLegacyController
# returns     True if downgrade successful, False otherwise
def upgrade_controller(legacy_controller):
    if type(legacy_controller) is TCPSocketController:
        Log.warning("upgrade_controller({}) controller hopeless".format(str(legacy_controller)))
        return False
    Log.debug("upgrade_controller({})".format(str(legacy_controller)))
    # Override those 2 methods (and make them bound to legacy_controller)
    legacy_controller.on_read_ready = types.MethodType(TCPSocketController.on_read_ready, legacy_controller)
    legacy_controller.on_send_data = types.MethodType(TCPSocketController.on_send_data, legacy_controller)
    return True

# Makes a TCPSocketController behave like a legacy controller
# controller  A TCPSocketController
# returns     True if downgrade successful, False otherwise
def downgrade_controller(controller):
    if type(controller) is TCPSocketLegacyController:
        Log.warning("downgrade_controller({}) controller hopeless".format(str(controller)))
        return False
    Log.debug("downgrade_controller({})".format(str(controller)))
    # Override those 2 methods (and make them bound to controller)
    controller.on_read_ready = types.MethodType(TCPSocketLegacyController.on_read_ready, controller)
    controller.on_send_data = types.MethodType(TCPSocketLegacyController.on_send_data, controller)
    return True

#
# A controller connected on the SocketConnectionManager
#
class TCPSocketController(Controller):
    def __init__(self, controllers_manager, conn, addr):
        super(TCPSocketController, self).__init__(controllers_manager)
        self.connection = conn
        self.address = addr
        self.buffer = bytearray([])
        self.initialize_selectible_fd(conn)

    def __str__(self):
        return str(self.address)

    # Called before the controller gets disconnected
    def destroy_selectible(self):
        try:
            self.connection.close()
        except: pass
        super(TCPSocketController, self).destroy_selectible()

    # Called when the socket has pending bytes to read
    def on_read_ready(self, cur_time_s, skip_recv=False):
        read = bytearray([])
        if not skip_recv:
            read = self.connection.recv(1024)
            if not read:
                return False
        try:
            self.buffer += read
            while len(self.buffer) >= 4:
                command_len = struct.unpack('<I', self.buffer[:4])[0]
                if len(self.buffer) >= 4 + command_len:
                    command = self.buffer[4:4+command_len]
                    self.buffer = self.buffer[4+command_len:]
                    loaded_json = json.loads(command.decode("utf-8"))
                    if type(loaded_json) is str: # ???? (some decoding shit)
                        loaded_json = json.loads(loaded_json)
                    self.on_command(loaded_json)
                elif self.buffer[3] != 0: # 4th byte not zero means its a HUGE buffer, i call BS
                    if not downgrade_controller(self):
                        return False
                    return self.on_read_ready(cur_time_s, skip_recv=True)
                else:
                    break
            return True
        except Exception as e:
            Log.warning("TCPSocketController::on_read_ready()", exception=True)
            return False

    # Called when data needs to be sent to the remote controller on the socket
    def on_send_data(self, json_data):
        try:
            json_data = json.dumps(json_data)
            msg = struct.pack('<I', len(json_data)) + bytearray(json_data.encode("utf-8"))
            self.write_to_fd(msg)
            return True
        except:
            Log.warning("TCPSocketController::on_send_data({}) Failed".format(str(json_data)), exception=True)
            return False

#
# A controller connected on the SocketConnectionManager using the legacy
# protocol (commands as newlines)
#
class TCPSocketLegacyController(TCPSocketController):
    def __init__(self, controllers_manager, conn, addr):
        super(TCPSocketLegacyController, self).__init__(controllers_manager, conn, addr)

    # Called when the socket has pending bytes to read
    def on_read_ready(self, cur_time_s, skip_recv=False):
        read = bytearray([])
        if not skip_recv:
            read = self.connection.recv(1024)
            if not read:
                return False
        try:
            self.buffer += read

            if ord("{") in self.buffer: # this character is NEVER sent on the legacy protocol, this must be a new controller!
                if not upgrade_controller(self):
                    return False
                return self.on_read_ready(cur_time_s, skip_recv=True)

            while True:
                try:
                    newline_idx = self.buffer.index(bytes([ord("\n")]))
                    if newline_idx >= 0:
                        command = self.buffer[:newline_idx+1].decode('utf-8')
                        self.buffer = self.buffer[newline_idx+1:]
                        if command == "S\n":
                            # Heartbeat support: just reply with garbage byte
                            self.write_to_fd(bytearray([0]))
                        else:
                            Log.hammoud("SocketLegacyController::on_read_ready({})".format(command))
                            m = re.search("^(?P<type>[atlfcs])(?P<index>[0-9]+):(?P<value>[0-9]+)\n$", command)
                            if m:
                                (t, index, value) = m.groups()
                                index = int(index)
                                value = int(value)
                                all_things = self.manager.controllers_manager.core.blueprint.get_things()
                                command_json = {}
                                if t == 'c':
                                    curtains = list(sorted(filter(lambda t: type(t) is Curtain, all_things), key=lambda t: t.id))
                                    if index <= len(curtains):
                                        command_json = {
                                            "thing": curtains[index].id,
                                            "curtain": value
                                        }
                                elif t == 't':
                                    switches = list(reversed(sorted(filter(lambda t: type(t) is LightSwitch, all_things), key=lambda t: t.id)))
                                    if index <= len(switches):
                                        command_json = {
                                            "thing": switches[index].id,
                                            "intensity": value
                                        }
                                elif t == 'l':
                                    dimmers = list(sorted(filter(lambda t: type(t) is Dimmer, all_things), key=lambda t: t.id))
                                    if index <= len(dimmers):
                                        command_json = {
                                            "thing": dimmers[index].id,
                                            "intensity": value
                                        }
                                elif t == 'a':
                                    acs = list(sorted(filter(lambda t: type(t) is CentralAC, all_things), key=lambda t: t.id))
                                    if index <= len(acs):
                                        command_json = {
                                            "thing": acs[index].id,
                                            "set_pt": float(value) / 2
                                        }
                                elif t == 'f':
                                    acs = list(sorted(filter(lambda t: type(t) is CentralAC, all_things), key=lambda t: t.id))
                                    if index <= len(acs):
                                        command_json = {
                                            "thing": acs[index].id,
                                            "fan": value
                                        }
                                elif t == 's':
                                    hotel_controls = list(sorted(filter(lambda t: type(t) is HotelControls, all_things), key=lambda t: t.id))
                                    if len(hotel_controls) > 0:
                                        hotel_controls = hotel_controls[0]
                                        if index >= 0 and index <= 1:
                                            command_json = {"thing": hotel_controls.id}
                                            if index == 0: command_json["do_not_disturb"] = value
                                            else: command_json["room_service"] = value
                                if command_json != {}:
                                    self.on_command(command_json)
                except:
                    break
            return True
        except Exception as e:
            Log.warning(str(e), exception=True)
            return False

    # Called when data needs to be sent to the remote controller on the socket
    def on_send_data(self, json_data):
        try:
            # HACK: read all things in the blueprint of the room and dump it on every update
            acs = []
            dimmers = []
            switches = []
            curtains = []
            hotel_cards = []

            all_things = self.manager.controllers_manager.core.blueprint.get_things()

            acs += list(filter(lambda t: type(t) is CentralAC, all_things))
            dimmers += list(filter(lambda t: type(t) is Dimmer, all_things))
            switches += list(filter(lambda t: type(t) is LightSwitch, all_things))
            curtains += list(filter(lambda t: type(t) is Curtain, all_things))

            acs = sorted(acs, key=lambda t: t.id)
            dimmers = sorted(dimmers, key=lambda t: t.id)
            switches = sorted(switches, key=lambda t: t.id, reverse=True)
            curtains = sorted(curtains, key=lambda t: t.id)

            hotel_controls = list(filter(lambda t: type(t) is HotelControls, all_things))
            if len(hotel_controls) > 0:
                hotel_cards += [hotel_controls[0].do_not_disturb, hotel_controls[0].room_service]

            msg = bytearray([254])
            msg += bytearray([len(acs)])
            for ac in acs:
                msg += bytearray([int(ac.current_fan_speed), int(ac.current_set_point*2), int(ac.current_temperature)])
            msg += bytearray([len(dimmers)] + list(map(lambda t: t.intensity, dimmers)))
            msg += bytearray([len(switches) + len(hotel_cards)] + list(map(lambda t: t.intensity, switches)) + hotel_cards)
            msg += bytearray([len(curtains), 255])
            self.write_to_fd(msg)
            return True
        except Exception as e:
            Log.warning("FAILED TCPSocketLegacyController::on_send_data({})".format(json_data), exception=True)
            return False
