import socket
import select

from config.general_config import GENERAL_CONFIG

class Serial(object):
    def __init__(self):
        self.sock = None
        self.buffered_bytes = bytearray([])
        self.socket_port = 9911

    def open(self):
        if self.sock != None:
            self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", self.socket_port))

    def close(self):
        try:
            self.sock.close()
        except:
            pass
        self.sock = None

    def write(self, bytes):
        if self.sock:
            return self.sock.send(bytes)
        return -1

    def read(self, num_bytes):
        while len(self.buffered_bytes) < num_bytes:
            x = self.in_waiting

        ret = self.buffered_bytes[:num_bytes]
        self.buffered_bytes = self.buffered_bytes[num_bytes:]
        return ret

    def fileno(self):
        return self.sock.fileno()

    def __getattribute__(self, name):
        if name == "in_waiting":
            (ready_socks, _, _) = select.select([self.sock], [], [], 0)
            if len(ready_socks) > 0:
                self.buffered_bytes += ready_socks[0].recv(1024)
            return len(self.buffered_bytes)
        else:
            return super(Serial, self).__getattribute__(name)

class FakeComPort:
    def __init__(self):
        self.serial_number = "123456789"
        self.vendor = GENERAL_CONFIG.SIMULATED_BOARD_NAME
        self.device = GENERAL_CONFIG.SIMULATED_BOARD_NAME

def comports():
    return [FakeComPort()]

