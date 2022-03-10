import random
from copy import deepcopy
from typing import List, Optional, Callable

import networkx as nx

from .device import Device, DeviceType
from .firmware import Firmware, FW_TYPE_A
from .iqueue import ReadQueue
from .clock import Clock

Watcher = Callable[[List[Device]], None]


def watcher(blocking: bool = False, clean_screen: bool = False, print_long_device: bool = False, print_dev_progress: bool = True):
    def _watcher(devices: List[Device]):
        msgs_in_queues = 0
        if clean_screen:
            print("\033[H\033[J", end="")

        print(64*'=')
        print(64*'=')

        for d in devices:
            if print_long_device:
                print(d)

            if print_dev_progress:
                if not d.upgrading:
                    print(f'{d.dev_id}: v{d.running_firmware.version}')
                else:
                    print(f'{d.dev_id}: {d._ongoing_upgrade.candidate_firmware.data_size - d._ongoing_upgrade.candidate_firmware.data.count(None)}')

            print(64*'-')
            msgs_in_queues += d._input_queue._q.size()
        print(f"in queues: {msgs_in_queues}")
        print()
        if blocking:
            input()

    return _watcher


class Simulator:
    def __init__(self, clock: Clock, devices: List[Device], shuffle: bool = False):
        self._watcher: Optional[Callable] = None
        self.devices = devices
        self.tick = 0
        self._clock = clock
        self.clock = self._clock.clock_view()
        self.shuffle: bool = shuffle

    def run_for(self, ticks):
        start_at: int = self._clock.now
        self.run_until(lambda _: self._clock.now - start_at >= ticks)

    def run_until(self, stop_condition):
        while not stop_condition(self.devices):
            if self._watcher is not None:
                self._watcher(self.devices)

            devs = random.sample(self.devices, len(self.devices)) if self.shuffle else self.devices
            for device in devs:
                device.tick()
            self._clock.tick()

        if self._watcher is not None:
            self._watcher(self.devices)

    def attach_watcher(self, watcher: Watcher):
        self._watcher = watcher

    def detach_watcher(self):
        self._watcher = None


class SimulationBuilder:
    def __init__(self):
        self._graph: Optional[nx.Graph] = None
        self._debug: bool = False
        self._queues_max_len = None

    def from_networkx_graph(self, graph) -> 'SimulationBuilder':
        self._graph = graph
        return self

    def with_default_running_firmware(self, firmware: Firmware) -> 'SimulationBuilder':
        self._default_running_firmware = firmware
        return self

    def with_default_device_type(self, device_type: DeviceType) -> 'SimulationBuilder':
        self._default_device_type = device_type
        return self

    def with_default_link_reliability(self, link_reliability: float) -> 'SimulationBuilder':
        self._default_link_reliability = link_reliability
        return self

    def with_debug(self, debug: bool = True) -> 'SimulationBuilder':
        self._debug = debug
        return self

    def with_bounded_queues(self, maxlen: Optional[int] = None) -> 'SimulationBuilder':
        self._queues_max_len = maxlen
        return self

    def build(self) -> Simulator:
        clock = Clock()
        cv = clock.clock_view()
        int_mapping = {v: k for k, v in enumerate(list(self._graph.nodes))}

        queues = {label: ReadQueue(cv, self._debug, maxlen=self._queues_max_len) for label in self._graph.nodes}
        colors = []
        d_fw = Firmware(self._default_device_type, 0, [])
        devices = [
            Device(
                dev_id=i,
                dev_type=self._graph.nodes[node_label].get('running_firmware', d_fw).fw_type,
                input_queue=queues[node_label],
                neighbors={
                    int_mapping[k]: queues[k].write_queue_for_writer(
                        writer_id=i,
                        write_reliability=self._graph.nodes[node_label].get('msg_success_rate', self._default_link_reliability)
                    )
                    for k in self._graph.adj[node_label]
                },
                running_firmware=self._graph.nodes[node_label].get('running_firmware', deepcopy(self._default_running_firmware)),
                clock=cv
            )
            for i, node_label in enumerate(self._graph.nodes)
        ]

        relabeled = nx.relabel_nodes(self._graph, int_mapping, copy=True)
        for n in relabeled:
            if relabeled.nodes[n].get('running_firmware', d_fw).fw_type == FW_TYPE_A:
                colors.append('#FF0000')
            else:
                colors.append('#00FF00')

        return Simulator(clock, devices)
