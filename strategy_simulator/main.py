import networkx as nx

from .firmware import FW_TYPE_A, Firmware, FW_TYPE_B
from .simulator import SimulationBuilder, watcher
from .utils import general_stopping_condition

fw_size = 10
grid_size = (3, 3)
graph: nx.Graph = nx.grid_2d_graph(*grid_size)

# chessboardify(graph, grid_size[0], grid_size[1], Firmware(FW_TYPE_A, 1, [i for i in range(fw_size)]), Firmware(FW_TYPE_B, 1, [100 + 2*i for i in range(fw_size)]))

graph.nodes[(0, 0)]["running_firmware"] = Firmware(FW_TYPE_A, 2, [2*i for i in range(fw_size)])
# graph.nodes[(grid_size[0]-1, 0)]["running_firmware"] = Firmware(FW_TYPE_B, 2, [100 + 2*i for i in range(fw_size)])
# graph.nodes[(0, grid_size[1]-1)]["running_firmware"] = Firmware(FW_TYPE_B, 1, [100 + i for i in range(fw_size)])


sb = SimulationBuilder()
sb.with_default_device_type(FW_TYPE_A)
sb.with_default_running_firmware(Firmware(FW_TYPE_A, 1, [i for i in range(10)]))
sb.with_default_link_reliability(1.0)
sb.from_networkx_graph(graph)
s = sb.build()
# s.attach_watcher(watcher(blocking=True, clean_screen=True, print_dev_progress=True))
s.run_until(lambda x: general_stopping_condition(x, dev_type=None))
print(s.clock.now)
