from strategy_simulator.test_utils import grid_single_type, setup_rng, grid_multi_type, \
    spaceship_multi_type, path_ended_multi_type, extract_stats

x = spaceship_multi_type(
    fw_size=10,
    link_reliability=1.0,
    log_messages=True,
    watch=False
)
print(extract_stats(x))

setup_rng()
x = grid_single_type(
    grid_size_x=10,
    grid_size_y=10,
    fw_size=10,
    link_reliability=0.99,
    log_messages=True
)
print(extract_stats(x))

x = grid_single_type(
    grid_size_x=10,
    grid_size_y=10,
    fw_size=10,
    link_reliability=0.9,
    log_messages=True
)
print(extract_stats(x))

x = grid_multi_type(
    grid_size_x=10,
    grid_size_y=10,
    fw_size=10,
    link_reliability=1.0,
    log_messages=True
)
print(extract_stats(x))


x = path_ended_multi_type(
    length=5,
    fw_size=10,
    link_reliability=1.0,
    log_messages=True
)
print(extract_stats(x))


def convergence_vs_network_size_square():
    for i in range(2, 31):
        sim = grid_single_type(i, i, 1024, 1, True)
        print(f"({i}x{i}")
        print(sim.clock.now)
        print(extract_stats(sim))


def convergence_vs_network_size_rect():
    for i in range(2, 31):
        sim = grid_single_type(10, i, 1024, 1, True)
        print(f"(10x{i}")
        print(sim.clock.now)
        print(extract_stats(sim))


def convergence_vs_reliability():
    for r in range(100, 79, -1):
        setup_rng()
        sim = grid_single_type(10, 10, 1024, r/100, True)
        print(f"lr: {r}%")
        print(sim.clock.now)
        print(extract_stats(sim))


def convergence_vs_reliability_multitype():
    setup_rng()
    for r in range(100, 79, -1):
        sim = grid_multi_type(15, 15, 1024, r/100, True)
        print(f"lr: {r}%")
        print(sim.clock.now)
        print(extract_stats(sim))


# convergence_vs_network_size_square()
# convergence_vs_network_size_rect()
# convergence_vs_reliability()
convergence_vs_reliability_multitype()
