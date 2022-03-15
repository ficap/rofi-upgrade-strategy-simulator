import asyncio
import time

import networkx as nx

from asyncio import Queue

from firmware import Firmware, FW_TYPE_A
from client import client, watcher, all_devices_pass
from device import Device

# TODO: implement handling of different fw_types


async def main():
    net: nx.Graph = nx.barbell_graph(10, 10)
    nx.nx_pydot.write_dot(net, 'network.dot')

    timeout = .25

    queues = [Queue() for _ in range(len(net))]
    devices = [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 2, list(range(0, 20, 2))), timeout=timeout)
        for i in [0]] + [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 1, list(range(10))), timeout=timeout)
        for i in range(1, len(net))
    ]

    coros = [d.loop() for d in devices] + [client(devices), watcher(0.1, devices), all_devices_pass(devices, 0.1, lambda x: x.running_firmware.version == 2)]

    await asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED)


start = time.time_ns()
asyncio.run(main())
took = time.time_ns() - start
took = took / 1000_000_000
print(f"it took {took} seconds in realtime")
