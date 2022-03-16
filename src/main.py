import asyncio
import time
from typing import Callable, Optional

import networkx as nx

from asyncio import Queue

from firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from client import client, watcher, all_devices_pass
from device import Device

# TODO: implement handling of different fw_types


def device_has_fw_ver(version: int, dev_type: Optional[int] = None) -> Callable[[Device], bool]:
    def _device_has_fw_ver(device: Device) -> bool:
        if dev_type is not None and device.dev_type != dev_type:
            return True
        return device.running_firmware.version == version

    return _device_has_fw_ver


async def main():
    net: nx.Graph = nx.barbell_graph(5, 5)
    nx.nx_pydot.write_dot(net, 'network.dot')

    timeout = .25
    msg_success_rate = 1.

    queues = [Queue() for _ in range(len(net))]
    devices = [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 2, list(range(0, 20, 2))), timeout=timeout, msg_success_rate=msg_success_rate)
        for i in [0]
    ] + [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 1, list(range(10))), timeout=timeout, msg_success_rate=msg_success_rate)
        for i in range(1, len(net)-1)
    ] + [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 1, list(range(0, 10, 1))), timeout=timeout, msg_success_rate=msg_success_rate)
        for i in [len(net)-1]
    ]

    coros = [d.loop() for d in devices] + [client(devices), watcher(0.1, devices), all_devices_pass(devices, 0.1, device_has_fw_ver(2))]

    await asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED)


start = time.time_ns()
asyncio.run(main())
took = time.time_ns() - start
took = took / 1000_000_000
print(f"it took {took} seconds in realtime")
