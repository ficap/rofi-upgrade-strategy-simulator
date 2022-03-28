from typing import List, Optional
from time import sleep

from device import Device
from client import watcher


class Simulator:
    def __init__(self, devices: List[Device], ):
        self.devices = devices
        self.tick = 0

    def run(self, ticks: Optional[int] = None, stop_condition=None):
        ticks = ticks or -1
        stop_condition = stop_condition or (lambda _: False)

        while self.tick != ticks:
#             watcher(self.devices)
            if stop_condition(self.devices):
#                 for dev in self.devices:
#                     print(dev.input_queue)
                return

            for device in self.devices:
                device.tick(self.tick)

            self.tick += 1


