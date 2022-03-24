import asyncio
import time
from typing import Callable, Optional

import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt

from asyncio import Queue

from firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from client import client, watcher, all_devices_pass
from device import Device
from utils import duration

# TODO: implement handling of different fw_types



def device_has_fw_ver(version: int, dev_type: Optional[int] = None) -> Callable[[Device], bool]:
    def _device_has_fw_ver(device: Device) -> bool:
        if dev_type is not None and device.dev_type != dev_type:
            return True
        return device.running_firmware.version == version

    return _device_has_fw_ver


async def main(net: nx.Graph = nx.barbell_graph(5, 5), timeout: float = .1, msg_success_rate: float = 1.):
    nx.nx_pydot.write_dot(net, 'network.dot')

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

    # coros = [d.loop() for d in devices] + [client(devices), watcher(0.1, devices), all_devices_pass(devices, 0.1, device_has_fw_ver(2))]
    coros = [d.loop() for d in devices] + [all_devices_pass(devices, 0.1, device_has_fw_ver(2))]
    coros = [asyncio.tasks.ensure_future(c) for c in coros]

    done, pending = await asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED)
    if len(pending) > 0:
        for p in pending:
            if p not in coros:
                print(f"unknown coro {p}")
            else:
                i = coros.index(p)
                if not devices[i].killed:
                    print("!!! not killed yet")
                    devices[i].kill()
                    print(f"killing {devices[i]}")
        await asyncio.wait(pending)




async def benchmark_msg_succ_rate_vs_time(network, rate_from: int, rate_to: int, rate_step: int = 1, samples: int = 100, device_timeout: float = 0.05, settling_timeout: float = 5.):
    xs = []
    ys = []

    for rate in range(rate_from, rate_to+1, rate_step):
        succ_rate = rate / 100.
        xs.append(succ_rate)

        start = time.time_ns()
        for sample in range(samples):
            try:
                await asyncio.wait_for(main(net=network, msg_success_rate=succ_rate, timeout=device_timeout), timeout=settling_timeout)
            except asyncio.TimeoutError:
                for t in filter(lambda t: not t.done(), asyncio.Task.all_tasks()):
                    print(t)

        ys.append((time.time_ns() - start)/1000_000_000_0)

    plt.figure(figsize=(5, 2.7))
    plt.plot(xs, xs, label='linear')
    plt.plot(xs, ys, label='data')
    plt.xlabel("message success rate")
    plt.ylabel("settling time")
    plt.title("Message success rate vs. settling time")
    plt.legend()
    plt.savefig("output.png")


took, result = duration(lambda: asyncio.run(benchmark_msg_succ_rate_vs_time(nx.complete_graph(15), 90, 100, 1, 100)))
print(f"benchmark_msg_succ_rate_vs_time took {took}")
