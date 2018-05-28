import socket
import select

from config.general_config import GENERAL_CONFIG
from config.hardware_config import HARDWARE_CONFIG

class FakeSerial(object):
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
    def __init__(self, serial, vendor, device):
        self.serial_number = serial
        self.vendor = vendor
        self.device = device

def fake_comports():
    return [FakeComPort("123456789", GENERAL_CONFIG.SIMULATED_BOARD_NAME, GENERAL_CONFIG.SIMULATED_BOARD_NAME)]

from serial.tools.list_ports import comports
from serial import *
if GENERAL_CONFIG.SIMULATE_ARDUINO:
    Serial = FakeSerial
    comports = fake_comports

EXTRA_FAKE_PORTS = []

if HARDWARE_CONFIG.SERIAL_PORTS:
    ports = HARDWARE_CONFIG.SERIAL_PORTS.split(',')
    for port in ports:
        (vendor, device) = port.split(':')
        vendor = vendor.strip()
        device = device.strip()
        EXTRA_FAKE_PORTS.append(FakeComPort('fake-'+device, vendor, device))

original_comports = comports
def override_comports():
    ports = original_comports()
    reserved_devices = list(map(lambda fcp: fcp.device, EXTRA_FAKE_PORTS))
    filtered = []
    for p in ports:
        if p.device not in reserved_devices:
            filtered.append(p)

    return filtered + EXTRA_FAKE_PORTS

comports = override_comports
