from controllers.connection_manager import ConnectionManager
from core.select_service import Selectible
from controllers.tcp_socket_controllers.tcp_socket_controller import TCPSocketController, TCPSocketLegacyController
from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

import socket
import netifaces

class TCPHostedSocket(Selectible):
    def __init__(self, connection_manager, interface, ip):
        self.connection_manager = connection_manager
        self.interface = interface
        self.ip = ip
        self.sock = TCPHostedSocket.create_server_socket(self.ip)
        if self.sock == None:
            raise 1
        self.initialize_selectible_fd(self.sock)

        self.controller_class = TCPSocketController
        if CONTROLLERS_CONFIG.LEGACY_MODE:
            self.controller_class = TCPSocketLegacyController

        self.connection_manager.register_server_sock(self.interface, self)
        Log.info("Listening on {}:{}".format(ip, CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT))

    def destroy_selectible(self):
        try:
            self.sock.close()
        except: pass
        self.connection_manager.deregister_server_sock(self.interface)
        super(TCPHostedSocket, self).destroy_selectible()

    def on_read_ready(self, cur_time_s):
        try:
            conn, addr = self.sock.accept()
            self.controller_class(self.connection_manager.controllers_manager, conn, addr) # registers itself
        except:
            Log.error("Failed to accept a connection", exception=True)
            return False
        return True

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

#
# A socket-based connection manager for controllers
#
class TCPSocketConnectionManager(ConnectionManager):
    def __init__(self, controllers_manager):
        super(TCPSocketConnectionManager, self).__init__(controllers_manager)
        self.server_socks = {} # dictionary of iface name -> TCPHostedSocket on that iface
        self.reconnect_timer = 0

    def register_server_sock(self, iface, s):
        self.server_socks[iface] = s

    def deregister_server_sock(self, iface):
        del self.server_socks[iface]

    # Remove interfaces no longer on the system (or their IPs changed) and add newly discovered ones
    # cur_time_s. Current time in seconds
    def update_hosting_interfaces(self, cur_time_s):
        # Check if some interfaces disconnected or new interfaces connected
        if cur_time_s >= self.reconnect_timer:
            self.reconnect_timer = cur_time_s + CONTROLLERS_CONFIG.SOCKET_SERVER_RECONNECT_TIMEOUT
            available_interfaces = TCPSocketConnectionManager.discover_interfaces()
            for iface in list(self.server_socks.keys()):
                matching_interfaces = list(filter(lambda i: i[0] == iface, available_interfaces))
                if len(matching_interfaces) == 0 or matching_interfaces[0][1] != self.server_socks[iface].ip: # either interface no longer available or IP has changed
                    self.server_socks[iface].destroy_selectible()
            for (iface, ip) in available_interfaces:
                if iface not in self.server_socks:
                    try: TCPHostedSocket(self, iface, ip) # registers itself
                    except: pass

    # non-blocking listening to new connections and connected controllers
    def update(self, cur_time_s):
        # fix the hosting interfaces
        self.update_hosting_interfaces(cur_time_s)

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
