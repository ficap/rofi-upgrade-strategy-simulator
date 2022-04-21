import time
from typing import Optional, Callable, List

import networkx as nx

from device import Device
from firmware import FW_TYPE_A, Firmware
from iqueue import Queue


def duration(function):
    start = time.time_ns()
    result = function()
    took = time.time_ns() - start
    took = took / 1000_000_000
    
    return took, result


def build_network(
        net: nx.Graph = nx.barbell_graph(5, 5),
        default_msg_success_rate: float = 1.,
        default_fw: Firmware = Firmware(FW_TYPE_A, 1, [i for i in range(10)]),
        default_timeout: int = 5,
        default_different_fw_type_cache_size: int = 10
):
    int_mapping = {v: k for k, v in enumerate(list(net.nodes))}

    queues = {label: Queue() for label in net.nodes}
    devices = [
        Device(
            i,
            net.nodes[node_label].get('running_firmware', default_fw).fw_type,
            queues[node_label],
            {int_mapping[k]: queues[k] for k in net.adj[node_label]},
            net.nodes[node_label].get('running_firmware', default_fw),
            msg_success_rate=net.nodes[node_label].get('msg_success_rate', default_msg_success_rate),
            timeout=net.nodes[node_label].get('timeout', default_timeout),
            different_fw_type_cache_size=net.nodes[node_label].get('different_fw_type_cache_size', default_different_fw_type_cache_size),

        ) for i, node_label in enumerate(net.nodes)
    ]

    return devices


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


def all_devices_pass(devices: List[Device], predicate: Callable[[Device], bool]) -> bool:
    for d in devices:
        if not predicate(d):
            return False

    return True


def general_stopping_condition(devs: List[Device]) -> bool:
    # no_messages = all_devices_pass(devs, no_messages_in_queue())
    fw_ver = all_devices_pass(devs, device_has_fw_ver(2))

    #     if not fw_ver and no_messages:
    #         raise NoMoreMessagesError()
    return fw_ver# and no_messages


def watcher(devices: List[Device]):
    msgs_in_queues = 0
    print("\033[H\033[J", end="")
    for d in devices:
        print(d)
        msgs_in_queues += d.input_queue.size()
    print(f"in queues: {msgs_in_queues}")
    print()
