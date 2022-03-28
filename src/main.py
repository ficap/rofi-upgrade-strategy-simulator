from typing import Callable, Optional

import networkx as nx
import matplotlib.pyplot as plt

from iqueue import Queue

from firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from client import client, watcher, all_devices_pass
from device import Device
from simulator import Simulator

# TODO: implement handling of different fw_types


def device_has_fw_ver(version: int, dev_type: Optional[int] = None) -> Callable[[Device], bool]:
    def _device_has_fw_ver(device: Device) -> bool:
        if dev_type is not None and device.dev_type != dev_type:
            return True
        return device.running_firmware.version == version

    return _device_has_fw_ver


def build_network(net: nx.Graph = nx.barbell_graph(5, 5), msg_success_rate: float = 1.):

    queues = [Queue() for _ in range(len(net))]
    devices = [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 2, list(range(0, 20, 2))), msg_success_rate=msg_success_rate)
        for i in [0]
    ] + [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 1, list(range(10))), msg_success_rate=msg_success_rate)
        for i in range(1, len(net)-1)
    ] + [
        Device(i, FW_TYPE_A, queues[i],
               {k: queues[k] for k in net[i]},
               Firmware(FW_TYPE_A, 1, list(range(0, 10, 1))), msg_success_rate=msg_success_rate)
        for i in [len(net)-1]
    ]

    return devices


def benchmark_msg_succ_rate_vs_time(network, rate_from: int, rate_to: int, rate_step: int = 1, samples: int = 100):
    nx.nx_pydot.write_dot(network, 'network.dot')

    xs = []
    ys = []

    for rate in range(rate_from, rate_to+1, rate_step):
        succ_rate = rate / 100.
        xs.append(succ_rate)

        ticks = 0
        for sample in range(samples):
            devices = build_network(net=network, msg_success_rate=succ_rate)
            
            simulator = Simulator(devices)
            simulator.run(100000, lambda devs: all_devices_pass(devs, device_has_fw_ver(2)))

            ticks += simulator.tick 

        ys.append(ticks/samples)

    plt.figure(figsize=(5, 2.7))
    plt.plot(xs, xs, label='linear')
    plt.plot(xs, ys, label='data')
    plt.xlabel("message success rate")
    plt.ylabel("settling time")
    plt.title("Message success rate vs. settling time")
    plt.legend()
    plt.savefig("output.png")


# benchmark_msg_succ_rate_vs_time(nx.complete_graph(15), 90, 100, 1, 100)
benchmark_msg_succ_rate_vs_time(nx.complete_graph(5), 50, 100, 1, 100)
