from strategy_simulator.test_utils import setup_rng, soft_assert, avg_runtime, grid_single_type, grid_multi_type, \
    barbell_single_type, barbell_multi_type

NET_CATEGORIES = {
    'grid': None,

}
# input:
# topotype, topodims, numfwtypes, fwsizes, linkreliability

# output:
# total runtime until cond holds, messages sent (by type), messages lost, remaining messages in queues, timeouts


soft_assert(grid_single_type(
    grid_size_x=10,
    grid_size_y=10,
    fw_size=10,
    link_reliability=1.0
).clock.now, 135, "10x10 FW_Ax10 1.0")

setup_rng()
soft_assert(avg_runtime(
    lambda: grid_single_type(
        grid_size_x=10,
        grid_size_y=10,
        fw_size=10,
        link_reliability=0.9
    ),
    20
), 834.3, "10x10 FW_Ax10 0.9")

setup_rng()
soft_assert(avg_runtime(
    lambda: grid_single_type(
        grid_size_x=10,
        grid_size_y=10,
        fw_size=10,
        link_reliability=0.99
    ),
    20
), 312.9, "10x10 FW_Ax10 0.99")


soft_assert(grid_multi_type(
    grid_size_x=10,
    grid_size_y=10,
    fw_size=10,
    link_reliability=1.0
).clock.now, 206, "10x10 FW_Bx10 1.0")


setup_rng()
soft_assert(avg_runtime(
    lambda: grid_multi_type(
        grid_size_x=10,
        grid_size_y=10,
        fw_size=10,
        link_reliability=0.99
    ),
    20
), 253.45, "10x10 FW_Bx10 0.99")


setup_rng()
soft_assert(avg_runtime(
    lambda: grid_multi_type(
        grid_size_x=10,
        grid_size_y=10,
        fw_size=10,
        link_reliability=0.9
    ),
    20
), 734.55, "10x10 FW_Bx10 0.9")

soft_assert(barbell_single_type(
    bell_size=5,
    path_length=5,
    fw_size=10,
    link_reliability=1.0
).clock.now, 118, "K5--P5--K5 FW_Bx10 1.0")

soft_assert(barbell_multi_type(
    bell_size=5,
    path_length=5,
    fw_size=10,
    link_reliability=1.0
).clock.now, 190, "1BK5--AP5--1BK5 FW_Bx10 1.0")

setup_rng()
soft_assert(avg_runtime(
    lambda: barbell_single_type(
        bell_size=5,
        path_length=5,
        fw_size=10,
        link_reliability=0.99
    ),
    20
), 698.55, "K5--P5--K5 FW_Ax10 0.99")

setup_rng()
soft_assert(avg_runtime(
    lambda: barbell_single_type(
        bell_size=5,
        path_length=5,
        fw_size=10,
        link_reliability=0.9
    ),
    20
), 1432.1, "K5--P5--K5 FW_Ax10 0.9")

setup_rng()
soft_assert(avg_runtime(
    lambda: barbell_multi_type(
        bell_size=5,
        path_length=5,
        fw_size=10,
        link_reliability=0.99
    ),
    20
), 416.2, "1BK5--P5--1BK5 FW_Bx10 0.99")

setup_rng()
soft_assert(avg_runtime(
    lambda: barbell_multi_type(
        bell_size=5,
        path_length=5,
        fw_size=10,
        link_reliability=0.9
    ),
    20
), 2811.75, "1BK5--P5--1BK5 FW_Bx10 0.9")
