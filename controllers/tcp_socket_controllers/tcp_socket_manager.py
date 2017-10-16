from controllers.connection_manager import ConnectionManager
from controllers.tcp_socket_controllers.tcp_socket_controller import TCPSocketController, TCPSocketLegacyController
from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

import socket
import netifaces
from select import select

#
# A socket-based connection manager for controllers
#
class TCPSocketConnectionManager(ConnectionManager):
    def __init__(self, controllers_manager):
        super(TCPSocketConnectionManager, self).__init__(controllers_manager)
        self.server_socks = {} # dictionary of iface name -> socket on that iface
        self.hosting_ips = {} # dictionary of iface name -> hosting IP (in case it changes)
        self.reconnect_timer = 0
        self.controller_class = TCPSocketController
        if CONTROLLERS_CONFIG.LEGACY_MODE:
            self.controller_class = TCPSocketLegacyController

    # Remove interfaces no longer on the system (or their IPs changed) and add newly discovered ones
    # cur_time_s. Current time in seconds
    def update_hosting_interfaces(self, cur_time_s):
        # Check if some interfaces disconnected or new interfaces connected
        if cur_time_s >= self.reconnect_timer:
            self.reconnect_timer = cur_time_s + CONTROLLERS_CONFIG.SOCKET_SERVER_RECONNECT_TIMEOUT
            available_interfaces = TCPSocketConnectionManager.discover_interfaces()
            for iface in list(self.server_socks.keys()):
                matching_interfaces = list(filter(lambda i: i[0] == iface, available_interfaces))
                if len(matching_interfaces) == 0 or matching_interfaces[0][1] != self.hosting_ips[iface]: # either interface no longer available or IP has changed
                    try: self.server_socks[iface].close()
                    except: pass
                    del self.server_socks[iface]
                    del self.hosting_ips[iface]
            for (iface, ip) in available_interfaces:
                if iface not in self.server_socks:
                    s = TCPSocketConnectionManager.create_server_socket(ip)
                    if s:
                        self.server_socks[iface] = s
                        self.hosting_ips[iface] = ip
                        Log.info("Listening on {}:{}".format(ip, CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT))

    # Performs a select on the connected sockets and performas the read operations
    # cur_time_s. Current time in seconds
    def read_sockets(self, cur_time_s):
        # perform a nonblocking select on server sockets and all connections
        controllers_descriptors = list(map(lambda c: c.connection, self.connected_controllers))
        server_descriptors = list(self.server_socks.values())
        try:
            (ready_descriptors, _, _) = select(server_descriptors + controllers_descriptors, [], [], 0)
            for desc in ready_descriptors:
                if desc in server_descriptors:
                    # a new client connected
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
                    # a controller has data to read
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

    # non-blocking listening to new connections and connected controllers
    def update(self, cur_time_s):
        # fix the hosting interfaces
        self.update_hosting_interfaces(cur_time_s)

        # read controllers sockets and accept any new connections
        self.read_sockets(cur_time_s)

        super(TCPSocketConnectionManager, self).update(cur_time_s)

    # Called when this manager needs to free all its resources
    def cleanup(self):
        super(TCPSocketConnectionManager, self).cleanup()
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
                if i in CONTROLLERS_CONFIG.SOCKET_HOSTING_INTERCACES:
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
