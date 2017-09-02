from hardware import HardwareManager
from logs import Log
import time

Log.initialize()

hw_manager = HardwareManager()

while True:
    cur_time_s = time.time()
    hw_manager.update(cur_time_s)

