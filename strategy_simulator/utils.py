from copy import deepcopy
from typing import Optional, Callable, List

from .device import Device


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
        return device._input_queue._q.size() == 0

    return _no_messages_in_queue


def all_devices_pass(devices: List[Device], predicate: Callable[[Device], bool]) -> bool:
    for d in devices:
        if not predicate(d):
            return False

    return True


def general_stopping_condition(devs: List[Device], dev_type=None) -> bool:
    # no_messages = all_devices_pass(devs, no_messages_in_queue())
    fw_ver = all_devices_pass(devs, device_has_fw_ver(2, dev_type))

    #     if not fw_ver and no_messages:
    #         raise NoMoreMessagesError()
    return fw_ver# and no_messages


def sum_queues_lengths(devs: List[Device], dev_type=None) -> int:
    if dev_type is not None:
        return sum(d._input_queue._q.size() for d in devs if d.dev_type == dev_type)

    return sum(d._input_queue._q.size() for d in devs)


def chessboardify(graph, rows, cols, fw_a, fw_b):
    for row in range(rows):
        for col in range(cols):
            if row % 2 == 0:
                if col % 2 == 0:
                    graph.nodes[(row, col)]["running_firmware"] = deepcopy(fw_a)
                else:
                    graph.nodes[(row, col)]["running_firmware"] = deepcopy(fw_b)
            else:
                if col % 2 == 0:
                    graph.nodes[(row, col)]["running_firmware"] = deepcopy(fw_b)
                else:
                    graph.nodes[(row, col)]["running_firmware"] = deepcopy(fw_a)


def msg_upper_bound(diff_type_nodes_cnt: int, graph_deg: int, chunks: int):
    return diff_type_nodes_cnt * graph_deg * chunks


def dev_types_in_net(net: List[Device]):
    dev_types = set()
    for dev in net:
        dev_types.add(dev.dev_type)

    return sorted(list(dev_types))
