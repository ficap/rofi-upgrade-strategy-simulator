import itertools
import random
from dataclasses import dataclass, field
from typing import Any, List, Iterable, Dict, Tuple

import networkx as nx

from .custom_nets import spaceship, radial, neighbors_iterated_hull
from .firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from .messages import AnnounceMessage, RequestMessage, DataMessage
from .simulator import Simulator, SimulationBuilder, watcher
from .utils import general_stopping_condition


def setup_rng():
    random.seed(123456789)


def soft_assert(actual, expected, msg):
    if actual == expected:
        return
    print(f"{msg}: expected: {expected} but got: {actual}")


def avg_runtime(simulation_factory, count: int):
    vals = [x.clock.now for x in repeated(simulation_factory, count)]
    return sum(vals) / count


def repeated(simulation_factory, repetitions: int):
    return [simulation_factory() for _ in range(repetitions)]


def grid_single_type(grid_size_x: int = 10, grid_size_y: int = 10, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False, seed_node: Tuple[int, int] = (0, 0)) -> Simulator:
    graph: nx.Graph = nx.grid_2d_graph(grid_size_x, grid_size_y)

    graph.nodes[seed_node]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=None))

    return s


def grid_single_type_center(grid_size_x: int = 10, grid_size_y: int = 10, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False) -> Simulator:
    graph: nx.Graph = nx.grid_2d_graph(grid_size_x, grid_size_y)

    graph.nodes[(grid_size_x//2, grid_size_y//2)]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=None))

    return s


def grid_single_type_center_radial(radius, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False, seed_position: str = "center") -> Simulator:
    seed_positions = ["center", "corner"]
    if seed_position not in seed_positions:
        raise ValueError(f"Invalid seed_position value: {seed_position}, choose one of: {seed_positions}")

    graph, center, corners = radial(radius)
    if seed_position == "center":
        seed_pos = center
    else:
        seed_pos = corners[0]

    graph.nodes[seed_pos]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=None))

    return s


def grid_multi_type_center_radial(radius, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False, seed_position: str = "center", num_b_devices: int = 2) -> Simulator:
    seed_positions = ["center"]
    if seed_position not in seed_positions:
        raise ValueError(f"Invalid seed_position value: {seed_position}, choose one of: {seed_positions}")

    if num_b_devices < 2 or num_b_devices > 5:
        raise ValueError(f"num_b_devices < 2, must be 2 = < x < 5")

    graph, center, corners = radial(radius)

    if seed_position == "center":
        seed_pos = center

    graph.nodes[seed_pos]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])
    for i in range(num_b_devices - 1):
        graph.nodes[corners[i]]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def grid_multi_type_center_radial_single_component(radius, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False, seed_position: str = "center", num_b_cols_devices: int = 1) -> Simulator:
    seed_positions = ["center"]
    if seed_position not in seed_positions:
        raise ValueError(f"Invalid seed_position value: {seed_position}, choose one of: {seed_positions}")

    if num_b_cols_devices < 1 or num_b_cols_devices > radius:
        raise ValueError(f"num_b_devices must be 1 =< x <= {radius}")

    graph, center, corners = radial(radius)

    if seed_position == "center":
        seed_pos = center

    bv1s = neighbors_iterated_hull(graph, [corners[0]], i=num_b_cols_devices-1)

    for dev in bv1s:
        graph.nodes[dev]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    graph.nodes[seed_pos]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def grid_multi_type(grid_size_x: int = 10, grid_size_y: int = 10, fw_size: int = 10, link_reliability: float = 1.0,
                    log_messages: bool = False, watch: bool = False) -> Simulator:
    graph: nx.Graph = nx.grid_2d_graph(grid_size_x, grid_size_y)

    graph.nodes[(0, 0)]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])
    graph.nodes[(0, grid_size_y - 1)]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)

    s = sb.build()
    s.shuffle = True

    if watch:
        s.attach_watcher(watcher(blocking=True))
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def barbell_single_type(bell_size: int = 10, path_length: int = 10, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False) -> Simulator:
    graph: nx.Graph = nx.barbell_graph(bell_size, path_length)

    graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.shuffle = True
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=None))

    return s


def barbell_multi_type(bell_size: int = 10, path_length: int = 10, fw_size: int = 10, link_reliability: float = 1.0,
                     log_messages: bool = False) -> Simulator:
    graph: nx.Graph = nx.barbell_graph(bell_size, path_length)

    graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])
    graph.nodes[2*bell_size + path_length - 1]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def spaceship_multi_type(fw_size: int = 10, link_reliability: float = 1.0,
                         log_messages: bool = False, watch: bool = False) -> Simulator:
    graph: nx.Graph = nx.Graph(spaceship())

    graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])
    graph.nodes[5]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    if watch:
        s.attach_watcher(watcher(blocking=True, ))
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def path_ended_multi_type(length: int = 5, fw_size: int = 10, link_reliability: float = 1.0,
                          log_messages: bool = False) -> Simulator:
    graph: nx.Graph = nx.path_graph(length)

    graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_B, 2, [2 * i for i in range(fw_size)])
    graph.nodes[length-1]["running_firmware"] = Firmware(FW_TYPE_B, 1, [1 * i for i in range(fw_size)])

    sb = SimulationBuilder()
    sb.with_default_device_type(FW_TYPE_A)
    sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
    sb.with_default_link_reliability(link_reliability)
    sb.with_debug(log_messages)
    sb.from_networkx_graph(graph)
    s = sb.build()
    s.run_until(lambda x:
                general_stopping_condition(x, dev_type=FW_TYPE_B))

    return s


def group_by_type(lst: Iterable[Any]):
    r = {}
    for i in lst:
        arr = r.setdefault(i.__class__.__name__, [])
        arr.append(i)

    return r


@dataclass
class Stats:
    runtime: int = 0
    num_devices: int = 0
    received_messages_by_type: Dict[Any, list] = field(default_factory=lambda: dict())
    sent_messages_by_type: Dict[Any, list] = field(default_factory=lambda: dict())
    lost_messages_by_type: Dict[Any, list] = field(default_factory=lambda: dict())
    overflowed_messages_by_type: Dict[Any, list] = field(default_factory=lambda: dict())
    announce_seen_store_max: List[int] = field(default_factory=lambda: list())
    datas_seen_store_max: List[int] = field(default_factory=lambda: list())
    in_flight_reqs_max: List[int] = field(default_factory=lambda: list())
    input_queue_max: List[int] = field(default_factory=lambda: list())
    # simulator: Optional[Simulator] = None

    def received_by_type_len(self, typee: Any):
        typee = typee if isinstance(typee, str) else typee.__name__
        return len(self.received_messages_by_type.get(typee, []))

    def sent_by_type_len(self, typee: Any):
        typee = typee if isinstance(typee, str) else typee.__name__
        return len(self.sent_messages_by_type.get(typee, []))

    def lost_by_type_len(self, typee: Any):
        typee = typee if isinstance(typee, str) else typee.__name__
        return len(self.lost_messages_by_type.get(typee, []))

    def overflowed_by_type_len(self, typee: Any):
        typee = typee if isinstance(typee, str) else typee.__name__
        return len(self.overflowed_messages_by_type.get(typee, []))

    def __str__(self):
        return f"R: " \
               f"A: {self.received_by_type_len(AnnounceMessage)}, " \
               f"R: {self.received_by_type_len(RequestMessage)}, " \
               f"D: {self.received_by_type_len(DataMessage)}\n" \
               f"S: " \
               f"A: {self.sent_by_type_len(AnnounceMessage)}, " \
               f"R: {self.sent_by_type_len(RequestMessage)}, " \
               f"D: {self.sent_by_type_len(DataMessage)}\n" \
               f"L: " \
               f"A: {self.lost_by_type_len(AnnounceMessage)}, " \
               f"R: {self.lost_by_type_len(RequestMessage)}, " \
               f"D: {self.lost_by_type_len(DataMessage)}\n" \
               f"O: " \
               f"A: {self.overflowed_by_type_len(AnnounceMessage)}, " \
               f"R: {self.overflowed_by_type_len(RequestMessage)}, " \
               f"D: {self.overflowed_by_type_len(DataMessage)}\n" \
               f"runtime: {self.runtime}\n" \
               f"Inputmax: {max(*self.input_queue_max)}\n" \
               f"Amax: {max(*self.announce_seen_store_max)}\n" \
               f"Rmax: {self.in_flight_reqs_max}\n" \
               f"Dmax: {max(*self.datas_seen_store_max)}\n"


def extract_stats(s: Simulator) -> Stats:
    runtime = s.clock.now
    devs = s.devices
    ll = [x.neighbors.values() for x in devs]
    lost_messages = [l._lost_messages for k in ll for l in k]
    sent_messages = [l._sent_messages for k in ll for l in k]
    overflowed_messages = [l._overflowed_messages for k in ll for l in k]
    received_messages = [x._input_queue._received_messages for x in devs]

    lost_by_type = group_by_type(itertools.chain().from_iterable(lost_messages))
    sent_by_type = group_by_type(itertools.chain().from_iterable(sent_messages))
    overflowed_by_type = group_by_type(itertools.chain().from_iterable(overflowed_messages))
    received_messages = group_by_type(i[1] for i in itertools.chain().from_iterable(received_messages))

    input_queue_max = [d._input_queue._q._max_used for d in devs]
    announce_seen_store_max = [d._diff_announces_seen_store._max_used_size for d in devs]
    datas_seen_store_max = [d._datas_seen_store._max_used_size for d in devs]
    in_flight_reqs_max = [d._in_flight_requests_store._max_used_size for d in devs]

    return Stats(
        runtime=runtime,
        num_devices=len(s.devices),
        received_messages_by_type=received_messages,
        sent_messages_by_type=sent_by_type,
        lost_messages_by_type=lost_by_type,
        overflowed_messages_by_type=overflowed_by_type,
        announce_seen_store_max=announce_seen_store_max,
        datas_seen_store_max=datas_seen_store_max,
        in_flight_reqs_max=in_flight_reqs_max,
        input_queue_max=input_queue_max
    )
