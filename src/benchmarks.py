from time import time
from typing import Callable, Optional, List, Tuple

import networkx as nx
import matplotlib.pyplot as plt

from iqueue import Queue

from firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from client import client, watcher, all_devices_pass
from device import Device
from simulator import Simulator


class NoMoreMessagesError(BaseException):
    pass


def device_has_fw_ver(version: int, dev_type: Optional[int] = None) -> Callable[[Device], bool]:
    def _device_has_fw_ver(device: Device) -> bool:
        if dev_type is not None and device.dev_type != dev_type:
            return True
        return device.running_firmware.version == version

    return _device_has_fw_ver


def no_messages_in_queue(dev_type: Optional[int] = None) -> Callable[[Device], bool]:
    def _no_messages_in_queue(device: Device) -> bool:
        if dev_type is not None and device.dev_type != dev_type:
            return True
        return device.input_queue.size() == 0

    return _no_messages_in_queue


def build_network(net: nx.Graph = nx.barbell_graph(5, 5), msg_success_rate: float = 1.):
    vertices = {v: k for k, v in enumerate(list(net.nodes))}
    net = net.adjacency()
    net = dict(list(map(lambda x: (vertices[x[0]], list(map(lambda y: vertices[y], x[1]))), net)))

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


def general_stopping_condition(devs: List[Device]) -> bool:
#     no_messages = all_devices_pass(devs, no_messages_in_queue())
    fw_ver = all_devices_pass(devs, device_has_fw_ver(2))

#     if not fw_ver and no_messages:
#         raise NoMoreMessagesError()
    return fw_ver


def make_graph(title: str, data: List[Tuple[str, List[float], List[float]]], xlabel: str, ylabel: str, filename: str, show: bool):
    plt.figure()
    for label, xs, ys in data:
        plt.plot(xs, ys, label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.savefig(filename)
    if show:
        plt.show()


def network_settling_time_vs_msg_succ_rate(network, rate_from: int, rate_to: int, rate_step: int = 1, 
                                           samples: int = 100, count_fails: bool = False):

    xs = []
    ys = []
    failed_simulations = []

    for rate in range(rate_from, rate_to + 1, rate_step):
        succ_rate = rate / 100.
        xs.append(succ_rate)

        ticks = 0
        fails = 0
        for sample in range(samples):
            devices = build_network(net=network, msg_success_rate=succ_rate)
            
            simulator = Simulator(devices)
            try:
                simulator.run(100000, general_stopping_condition)
                ticks += simulator.tick 
            except NoMoreMessagesError:
                if count_fails:
                    fails += 1
                else:
                    raise

        ys.append(ticks/(samples-fails+1))  # prevent division by zero
        failed_simulations.append(fails)

    if not count_fails:
        return xs, ys
    else:
        return xs, ys, failed_simulations


def benchmark_settling_time_vs_network_size_vs_succ_rate(networks, rate_from: int, rate_to: int, rate_step: int, samples: int = 100, note: str = ""):
    now = time()

    data = []

    for network in networks:
        nx.nx_pydot.write_dot(network, f"bench-settling-time-vs-network-size-vs-succ-rate{len(network)}-{note}-{rate_from}-{rate_to}-{rate_step}-{samples}-{now}.dot")
        xs, ys = network_settling_time_vs_msg_succ_rate(network, rate_from, rate_to, rate_step, samples, False)

        data.append((f"{len(network)}", xs, ys))
        
    make_graph(
        "Settling Time vs. Messages Success Rate", 
        data, 
        "Message Success Rate", 
        "Settling Time", 
        f"bench-msg-succ-rate-vs-time-vs-succ-rate{note}-{rate_from}-{rate_to}-{rate_step}-{samples}-{now}.png", 
        True
    )


def benchmark_settling_time_vs_network_size(networks, samples: int = 100, note: str = ""):
    now = time()

    xs = []
    ys = []

    for network in networks:
        nx.nx_pydot.write_dot(network, f"bench-settling-time-vs-network-size-{now}-{len(network)}-{note}-{samples}.dot")
        _, ys1 = network_settling_time_vs_msg_succ_rate(network, 100, 100, 1, samples, False)

        xs.append(len(network))
        ys.append(ys1)
        
    make_graph(
        "Settling Time vs. Messages Success Rate", 
        [
            ("data", xs, ys),
            ("linear", xs, xs)
        ], 
        "Network Size", 
        "Settling Time", 
        f"bench-settling-time-vs-network-size-{now}-{note}-{samples}.png", 
        True
    )

