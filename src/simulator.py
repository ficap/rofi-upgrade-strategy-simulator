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
#             sleep(0.2)

            for device in self.devices:
                device.tick(self.tick)

            if stop_condition(self.devices):
#                 for dev in self.devices:
#                     print(dev.input_queue)
                return

            self.tick += 1


