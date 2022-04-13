from time import time
from typing import List, Tuple

import networkx as nx
import matplotlib.pyplot as plt

from simulator import Simulator
from utils import build_network, general_stopping_condition


class NoMoreMessagesError(BaseException):
    pass


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
            devices = build_network(net=network, default_msg_success_rate=succ_rate)
            
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

