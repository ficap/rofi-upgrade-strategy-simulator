import networkx as nx

from simulator import Simulator
from firmware import Firmware, FW_TYPE_A, FW_TYPE_B
from utils import build_network, general_stopping_condition

from benchmarks import benchmark_settling_time_vs_network_size_vs_succ_rate, benchmark_settling_time_vs_network_size

# todo: for all following benchmarks specify device with higher firmware version like so
# todo: graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2*i for i in range(10)])
# benchmark_msg_succ_rate_vs_time(nx.grid_2d_graph(m=10, n=10), 50, 100, 1, 100, "grid_2d_graph(10.10)")
# benchmark_settling_time_vs_network_size_vs_succ_rate([nx.grid_2d_graph(i, i) for i in range(3, 11)], 80, 100, 1, 500, "grid")
# benchmark_settling_time_vs_network_size([nx.grid_2d_graph(i, i) for i in range(3, 30)], 50, "grid")

# benchmark_msg_succ_rate_vs_time(nx.complete_graph(5), 50, 100, 1, 1000, "complete_graph(5)")
# benchmark_msg_succ_rate_vs_time(nx.barbell_graph(5, 5), 50, 100, 1, 100, "barbell_graph(5,5)")

# graph: nx.Graph = nx.barbell_graph(5, 5)
# graph.nodes[0]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2*i for i in range(10)])
# graph.nodes[1]["running_firmware"] = Firmware(FW_TYPE_B, 2, [100 + 2*i for i in range(10)])
# graph.nodes[len(graph.nodes)-1]["running_firmware"] = Firmware(FW_TYPE_B, 1, [100 + i for i in range(10)])

graph: nx.Graph = nx.grid_2d_graph(7, 7)
graph.nodes[(0, 0)]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2*i for i in range(10)])
graph.nodes[(6, 0)]["running_firmware"] = Firmware(FW_TYPE_B, 2, [100 + 2*i for i in range(10)])
graph.nodes[(6, 6)]["running_firmware"] = Firmware(FW_TYPE_B, 1, [100 + i for i in range(10)])

net = build_network(graph, default_msg_success_rate = 0.9)
simulator = Simulator(net)

simulator.run(stop_condition=general_stopping_condition)
