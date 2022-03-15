import asyncio
import networkx as nx

from asyncio import Queue

from firmware import Firmware, FW_TYPE_A
from client import client, watcher
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

    coros = [d.loop() for d in devices] + [client(devices), watcher(0.5, devices)]
    
    await asyncio.gather(*coros)


asyncio.run(main())
