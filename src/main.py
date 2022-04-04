import networkx as nx

from benchmarks import benchmark_settling_time_vs_network_size_vs_succ_rate, benchmark_settling_time_vs_network_size

# TODO: implement handling of different fw_types

# benchmark_msg_succ_rate_vs_time(nx.grid_2d_graph(m=10, n=10), 50, 100, 1, 100, "grid_2d_graph(10.10)")
# benchmark_settling_time_vs_network_size_vs_succ_rate([nx.grid_2d_graph(i, i) for i in range(3, 11)], 80, 100, 1, 500, "grid")
benchmark_settling_time_vs_network_size([nx.grid_2d_graph(i, i) for i in range(3, 30)], 50, "grid")

# benchmark_msg_succ_rate_vs_time(nx.complete_graph(5), 50, 100, 1, 1000, "complete_graph(5)")
# benchmark_msg_succ_rate_vs_time(nx.barbell_graph(5, 5), 50, 100, 1, 100, "barbell_graph(5,5)")
