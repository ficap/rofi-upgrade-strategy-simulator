import networkx as nx


def spaceship():
    #        1----3
    #       /|    |\
    #      0B|    | 5B
    #       \|    |/
    #        2----4

    return {
        0: [1, 2],
        1: [0, 2],
        2: [0, 1],
        3: [1, 4],
        4: [2, 3],
        5: [3, 4]
    }


def radial(radius):
    dim = 2

    dims = [radius * 2 + 1] * dim
    g: nx.Graph = nx.grid_graph(dims)
    center = tuple(x//2 for x in dims)

    corners = [(radius, 0), (-radius, 0), (0, radius), (0, -radius)]
    corners = [tuple(map(sum, zip(center, corners[i]))) for i in range(2**dim)]

    a = nx.single_source_shortest_path_length(g, center)
    g = g.subgraph([node for node, length in a.items() if length <= radius])

    return g, center, corners


def neighbors_iterated_hull(g: nx.Graph, nodes: list, i: int = 1):
    tmp = set(nodes)
    for j in range(i):
        tmp = tmp.union(set().union(*(g.neighbors(n) for n in tmp)))

    return tmp
