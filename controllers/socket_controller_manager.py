from controllers.connection_manager import ConnectionManager
from controllers.controller import Controller
from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

from things.air_conditioner import CentralAC
from things.light import LightSwitch, Dimmer
from things.curtain import Curtain

import socket
import struct
import json
import re
import netifaces
import types
from select import select

#
# A controller connected on the SocketConnectionManager
#
class SocketController(Controller):
    def __init__(self, connection_manager, conn, addr):
        super(SocketController, self).__init__(connection_manager)
        self.connection = conn
        self.address = addr
        self.buffer = bytearray([])

    def __str__(self):
        return str(self.address)

    # Called before the controller gets disconnected
    def disconnect(self):
        super(SocketController, self).disconnect()
        try:
            self.connection.close()
        except: pass

    # Makes a SocketLegacyController behave like a non-legacy controller
    # controller  A SocketLegacyController
    @staticmethod
    def upgrade_controller(legacy_controller):
        Log.debug("SocketController::upgrade_controller({})".format(str(legacy_controller)))
        # Override those 2 methods (and make them bound to legacy_controller)
        legacy_controller.on_read_data = types.MethodType(SocketController.on_read_data, legacy_controller)
        legacy_controller.on_send_data = types.MethodType(SocketController.on_send_data, legacy_controller)

    # Called when the socket has pending bytes to read
    def on_read_data(self):
        read = self.connection.recv(1024)
        if not read:
            return False
        try:
            self.buffer += read
            if len(self.buffer) >= 4:
                command_len = struct.unpack('<I', self.buffer[:4])[0]
                if len(self.buffer) >= 4 + command_len:
                    command = self.buffer[4:4+command_len]
                    self.buffer = self.buffer[4+command_len:]
                    loaded_json = json.loads(command.decode("utf-8"))
                    if type(loaded_json) is str: # ???? (some decoding shit)
                        loaded_json = json.loads(loaded_json)
                    self.on_command(loaded_json)
                elif self.buffer[:4] == bytearray([ord('S'), ord('\n'), ord('S'), ord('\n')]): # this is a legacy controller!
                    SocketLegacyController.downgrade_controller(self)
                    return True
                elif self.buffer[3] != 0: # 4th byte not zero means its a HUGE buffer, i call BS
                    Log.warning("SocketController::on_read_data() detected very huge load (likely a compatibility issue)")
                    return False
            return True
        except Exception as e:
            Log.warning("SocketController::on_read_data()", exception=True)
            return False

    # Called when data needs to be sent to the remote controller on the socket
    def on_send_data(self, json_data):
        try:
            json_data = json.dumps(json_data)
            msg = struct.pack('<I', len(json_data)) + bytearray(json_data.encode("utf-8"))
            self.connection.send(msg)
            return True
        except:
            Log.warning("SocketController::on_send_data({}) Failed".format(str(json_data)), exception=True)
            return False

#
# A controller connected on the SocketConnectionManager using the legacy
# protocol (commands as newlines)
#
class SocketLegacyController(SocketController):
    def __init__(self, connection_manager, conn, addr):
        super(SocketLegacyController, self).__init__(connection_manager, conn, addr)

    # Makes a SocketController behave like a legacy controller
    # controller  A SocketController
    @staticmethod
    def downgrade_controller(controller):
        Log.debug("SocketLegacyController::downgrade_controller({})".format(str(controller)))
        # Override those 2 methods (and make them bound to controller)
        controller.on_read_data = types.MethodType(SocketLegacyController.on_read_data, controller)
        controller.on_send_data = types.MethodType(SocketLegacyController.on_send_data, controller)

    # Called when the socket has pending bytes to read
    def on_read_data(self):
        read = self.connection.recv(1024)
        if not read:
            return False
        try:
            self.buffer += read

            if ord("{") in self.buffer: # this character is NEVER sent on the legacy protocol, this must be a new controller!
                SocketController.upgrade_controller(self)
                return True

            while True:
                try:
                    newline_idx = self.buffer.index(bytes([ord("\n")]))
                    if newline_idx >= 0:
                        command = self.buffer[:newline_idx+1].decode('utf-8')
                        self.buffer = self.buffer[newline_idx+1:]
                        if command == "S\n":
                            # Heartbeat support: just reply with garbage byte
                            self.connection.send(bytearray([0]))
                        else:
                            Log.hammoud("SocketLegacyController::on_read_data({})".format(command))
                            m = re.search("^(?P<type>[atlfc])(?P<index>[0-9]+):(?P<value>[0-9]+)\n$", command)
                            if m:
                                (t, index, value) = m.groups()
                                index = int(index)
                                value = int(value)
                                all_things = self.manager.controllers_manager.core.blueprint.get_things()
                                command_json = {}
                                if t == 'c':
                                    curtains = list(sorted(filter(lambda t: t.get_blueprint_tag() == Curtain.get_blueprint_tag(), all_things), key=lambda t: t.id))
                                    if index <= len(curtains):
                                        command_json = {
                                            "thing": curtains[index].id,
                                            "curtain": value
                                        }
                                elif t == 't':
                                    switches = list(reversed(sorted(filter(lambda t: t.get_blueprint_tag() == LightSwitch.get_blueprint_tag(), all_things), key=lambda t: t.id)))
                                    if index <= len(switches):
                                        command_json = {
                                            "thing": switches[index].id,
                                            "intensity": value
                                        }
                                elif t == 'l':
                                    dimmers = list(sorted(filter(lambda t: t.get_blueprint_tag() == Dimmer.get_blueprint_tag(), all_things), key=lambda t: t.id))
                                    if index <= len(dimmers):
                                        command_json = {
                                            "thing": dimmers[index].id,
                                            "intensity": value
                                        }
                                elif t == 'a':
                                    acs = list(sorted(filter(lambda t: t.get_blueprint_tag() == CentralAC.get_blueprint_tag(), all_things), key=lambda t: t.id))
                                    if index <= len(acs):
                                        command_json = {
                                            "thing": acs[index].id,
                                            "set_pt": float(value) / 2
                                        }
                                elif t == 'f':
                                    acs = list(sorted(filter(lambda t: t.get_blueprint_tag() == CentralAC.get_blueprint_tag(), all_things), key=lambda t: t.id))
                                    if index <= len(acs):
                                        command_json = {
                                            "thing": acs[index].id,
                                            "fan": value
                                        }
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
            for room in self.manager.controllers_manager.core.blueprint.rooms:
                acs += room.get(CentralAC.get_blueprint_tag(), [])
                dimmers += room.get(Dimmer.get_blueprint_tag(), [])
                switches += room.get(LightSwitch.get_blueprint_tag(), [])
                curtains += room.get(Curtain.get_blueprint_tag(), [])
            acs = sorted(acs, key=lambda t: t.id)
            dimmers = sorted(dimmers, key=lambda t: t.id)
            switches = sorted(switches, key=lambda t: t.id, reverse=True)
            curtains = sorted(curtains, key=lambda t: t.id)
            msg = bytearray([254])
            msg += bytearray([len(acs)])
            for ac in acs:
                msg += bytearray([int(ac.current_fan_speed), int(ac.current_set_point*2), int(ac.current_temperature)])
            msg += bytearray([len(dimmers)] + list(map(lambda t: t.intensity, dimmers)))
            msg += bytearray([len(switches)] + list(map(lambda t: t.intensity, switches)))
            msg += bytearray([len(curtains), 255])
            self.connection.send(msg)
            return True
        except Exception as e:
            Log.warning("FAILED SocketLegacyController::on_send_data({})".format(json_data), exception=True)
            return False

#
# A socketIO-based connection manager for controllers
#
class SocketConnectionManager(ConnectionManager):
    def __init__(self, controllers_manager):
        super(SocketConnectionManager, self).__init__(controllers_manager)
        self.server_socks = {} # dictionary of iface name -> socket on that iface
        self.reconnect_timer = 0
        self.controller_class = SocketController
        if CONTROLLERS_CONFIG.LEGACY_MODE:
            self.controller_class = SocketLegacyController

    # non-blocking listening to new connections and connected controllers
    def update(self, cur_time_s):
        # Check if some interfaces disconnected or new interfaces connected
        if cur_time_s >= self.reconnect_timer:
            self.reconnect_timer = cur_time_s + CONTROLLERS_CONFIG.SOCKET_SERVER_RECONNECT_TIMEOUT
            available_interfaces = SocketConnectionManager.discover_interfaces()
            for iface in list(self.server_socks.keys()):
                if iface not in list(map(lambda iface: iface[0], available_interfaces)):
                    try: self.server_socks[iface].close()
                    except: pass
                    del self.server_socks[iface]
            for (iface, ip) in available_interfaces:
                if iface not in self.server_socks:
                    s = SocketConnectionManager.create_server_socket(ip)
                    if s:
                        self.server_socks[iface] = s
                        Log.info("Listening on {}:{}".format(ip, CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT))

        # perform a nonblocking select on server sockets and all connections
        controllers_descriptors = list(map(lambda c: c.connection, self.connected_controllers))
        server_descriptors = list(self.server_socks.values())
        try:
            (ready_descriptors, _, _) = select(server_descriptors + controllers_descriptors, [], [], 0)
            for desc in ready_descriptors:
                if desc in server_descriptors:
                    for iface in self.server_socks.keys():
                        if self.server_socks[iface] == desc:
                            try:
                                conn, addr = desc.accept()
                                self.register_controller(self.controller_class(self, conn, addr))
                            except:
                                Log.error("Failed to accept a connection", exception=True)
                                try: desc.close()
                                except: pass
                                del self.server_socks[iface]
                            break
                else:
                    for controller in self.connected_controllers:
                        if controller.connection == desc:
                            try:
                                if not controller.on_read_data():
                                    self.disconnect_controller(controller)
                            except Exception as e:
                                Log.warning("", exception=True)
                                self.disconnect_controller(controller)
        except Exception as e:
            Log.error("Unexpected error", exception=True)
            self.cleanup()

        super(SocketConnectionManager, self).update(cur_time_s)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        super(SocketConnectionManager, self).cleanup()
        for iface in self.server_socks:
            try: self.server_socks[iface].close()
            except: pass
        self.server_socks = {}

    # Discovers network interfaces active on this machine
    # returns  A list of tuples (interface_name, ip address)
    @staticmethod
    def discover_interfaces():
        ifaces = []
        for i in netifaces.interfaces():
            try:
                ip = netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr']
                sip = ip.split('.')
                if (int(sip[0]) > 160 and int(sip[0]) < 250 and int(sip[1]) != 254) or (int(sip[0]) == 10 and int(sip[1]) == 10):
                    ifaces.append((i, ip))
            except: pass
        return ifaces

    # Creates and binds a server socket on a given ip
    # ip  IP to bind the server socket to
    # returns  The create server socket
    @staticmethod
    def create_server_socket(ip):
        s = None
        try:
            addr = (ip, CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(addr)
            s.listen(CONTROLLERS_CONFIG.SOCKET_SERVER_MAX_CONNECTIONS)
        except Exception as e:
            Log.error(str(e), exception=True)
            try:
                s.close()
            except: pass
            s = None
        return s
