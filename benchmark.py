import gc
from functools import partial
from typing import List, Tuple, Any

import numpy as np

from strategy_simulator.messages import AnnounceMessage, DataMessage, RequestMessage
from strategy_simulator.test_utils import grid_single_type, setup_rng, extract_stats, grid_single_type_center, \
    grid_multi_type, grid_single_type_center_radial, grid_multi_type_center_radial, barbell_single_type, \
    grid_multi_type_center_radial_single_component
import matplotlib.pyplot as plt


# gc.disable()

def make_graph(title: str, data: List[Tuple[str, List[float], List[float]]], xlabel: str, ylabel: str, filename: str, show: bool):
    plt.figure()
    colors = plt.cm.rainbow(np.linspace(0, 1, len(data)))
    colors = iter(colors)
    for label, xs, ys in data:
        color = next(colors)
        plt.plot(xs, ys, label=label, c=color, marker="o")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.savefig(filename)
    if show:
        plt.show()


def avg(x):
    return sum(x)/len(x)


def grid_size_vs_time():
    setup_rng()
    stats = []
    for i in range(2, 6):
        reruns = []
        for rerun in range(20):
            print(f'rr{rerun}, i{i}')
            x = grid_single_type(
                grid_size_x=i,
                grid_size_y=i,
                fw_size=1024,
                link_reliability=.99,
                log_messages=True
            )
            reruns.append(extract_stats(x))

        stats.append((i*i, reruns))
    make_graph("Grid size vs time", [("data", [x[0] for x in stats], [avg([y.runtime for y in x[1]]) for x in stats])], "Network Size", "Time needed", "blah.pdf", True)


def grid_long_size_vs_time():
    setup_rng()
    stats = []
    for i in range(1, 50):
        reruns = []
        for rerun in range(5):
            print(f'rr{rerun}, i{i}')
            x = grid_single_type(
                grid_size_x=1,
                grid_size_y=i,
                fw_size=128,
                link_reliability=1.0,
                log_messages=True
            )
            reruns.append(extract_stats(x))

        stats.append((1*i, reruns))
    make_graph("Grid size vs time", [("data", [x[0] for x in stats], [avg([y.runtime for y in x[1]]) for x in stats])], "Network Size", "Time needed", "blah.png", True)
# grid_size_vs_time()


def grid_long_size_vs_time_vs_err():
    # message loss influence on convergence time + network size influence on convergence time
    setup_rng()
    stats = []
    for err in range(10):
        stats_err = []
        for grid_y in range(2, 25):
            reruns = []
            for rerun in range(10):
                print(f'err: {err} grid_y: {grid_y} rerun: {rerun}')
                x = grid_single_type(
                    grid_size_x=5,
                    grid_size_y=grid_y,
                    fw_size=32,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((grid_y, reruns))
        stats.append((err, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"msg loss: {err}%", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Grid Size 5*x",
               "Convergence Time", "grid_longx5_size_vs_time_vs_err-fwsize32.png", True)


def grid_long_size_vs_time_vs_grid_x():
    # network size influence on convergence time
    setup_rng()
    stats = []
    for grid_x in [(5, 4), (9, 4)]:
        stats_err = []
        for grid_y in range(5, 15):
            reruns = []
            for rerun in range(20):
                print(f'grid_x: {grid_x} grid_y: {grid_y} rerun: {rerun}')
                x = grid_single_type(
                    grid_size_x=grid_x[0],
                    grid_size_y=grid_y,
                    fw_size=32,
                    link_reliability=1.0,
                    log_messages=True,
                    seed_node=(grid_x[1], grid_y-1)
                )
                reruns.append(extract_stats(x))

            stats_err.append((grid_y, reruns))
        stats.append((grid_x[0], stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"grid: {err}*Grid Size Y", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Grid Size Y",
               "Convergence Time", "grid_xy_size_vs_time.png", True)


def grid_radial_size_vs_time_vs_err():
    # network size influence on convergence time
    setup_rng()
    stats = []
    errs = list(range(11))
    errs.extend(range(20, 110, 10))
    for err in errs:
        stats_err = []
        for radius in range(2, 15):
            reruns = []
            for rerun in range(5):
                print(f'err: {err} radius: {radius} rerun: {rerun}')
                x = grid_single_type_center_radial(
                    radius=radius,
                    fw_size=32,
                    link_reliability=1.0 - (err / 1000.0),
                    log_messages=True,
                )
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        stats.append((err, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"loss: {err/10.0} %", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Number of Modules",
               "Convergence Time", "grid_radial_size_vs_time_vs_errrrun5.png", True)


def grid_radial_size_vs_time():
    # network size influence on convergence time
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        for radius in range(2, 15):
            reruns = []
            for rerun in range(10):
                print(f'err: {err} radius: {radius} rerun: {rerun}')
                x = grid_single_type_center_radial(
                    radius=radius,
                    fw_size=32,
                    link_reliability=1.0 - (err / 1000.0),
                    log_messages=True,
                )
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        stats.append((err, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"loss: {err/10.0} %", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Number of Modules",
               "Convergence Time", "grid_radial_size_vs_timerrun10.pdf", True)


def multi_grid_radial_size_vs_time():
    # network size influence on convergence time
    setup_rng()
    stats = []
    for num_b_devices in range(2, 6):
        stats_err = []
        for radius in range(2, 15):
            reruns = []
            for rerun in range(10):
                print(f'err: {num_b_devices} radius: {radius} rerun: {rerun}')
                x = grid_multi_type_center_radial(
                    radius=radius,
                    fw_size=32,
                    link_reliability=1.0,
                    log_messages=True,
                    num_b_devices=num_b_devices
                )
                print(extract_stats(x))
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        stats.append((num_b_devices, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"Type B Modules: {err}", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Total Number of Modules",
               "Convergence Time", "multi_grid_radial_size_vs_timerrun10_upto_5_Bdevs32fwsize-request100-bigger.pdf", True)


def multi_grid_radial_size_vs_time_single_component():
    # network size influence on convergence time single component to update in corner
    setup_rng()
    stats = []
    for num_b_cols_devices in range(1, 6):
        stats_err = []
        for radius in range(5, 15):
            reruns = []
            for rerun in range(10):
                print(f'err: {num_b_cols_devices} radius: {radius} rerun: {rerun}')
                x = grid_multi_type_center_radial_single_component(
                    radius=radius,
                    fw_size=32,
                    link_reliability=1.0,
                    log_messages=True,
                    num_b_cols_devices=num_b_cols_devices
                )
                print(extract_stats(x))
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        bdevs = num_b_cols_devices/2*(2+(num_b_cols_devices-1)*2)
        stats.append((bdevs+1, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"Type B Modules: {err}", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Total Number of Modules",
               "Convergence Time", "multi_grid_radial_size_vs_timerrun10_Bdevs32fwsize-request100-touching-wmarkers-ann100-biggerhalfreqstore.pdf", True)


def grid_radial_size_vs_time_vs_seed_position():
    # network size influence on convergence time
    setup_rng()
    stats = []
    for seed_pos in ["center", "corner"]:
        stats_err = []
        for radius in range(2, 15):
            reruns = []
            for rerun in range(10):
                print(f'seed_pos: {seed_pos} radius: {radius} rerun: {rerun}')
                x = grid_single_type_center_radial(
                    radius=radius,
                    fw_size=32,
                    link_reliability=1.0,
                    log_messages=True,
                    seed_position=seed_pos
                )
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        stats.append((seed_pos, stats_err))

    make_graph("Grid Size and Convergence Time",
               [(f"seed position: {err}", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Number of Modules",
               "Convergence Time", "grid_radial_size_vs_timerrun10_vs_single_component.pdf", True)


def radial_fwsize_vs_time_vs_radius():
    # influence of firmware size on convergence time + influence of network size on convergence time
    setup_rng()
    stats = []
    for radius in range(3, 8):
        stats_err = []
        for fwsize in range(64, 512 + 1, 64):

            reruns = []
            for rerun in range(5):
                print(f'fwsize: {fwsize} r: {radius}, rerun: {rerun}')
                x = grid_single_type_center_radial(
                    radius=radius,
                    fw_size=fwsize,
                    link_reliability=1.0,
                    log_messages=True,
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((radius, stats_err))

    make_graph("Firmware Size and Convergence Time",
               [(f"r: {err} ({stats_err[0][1][0].num_devices} modules)", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Firmware Size",
               "Convergence Time", "grid_longx5_size_vs_time_vs_fwsize.pdf", True)


def simulation_graph(
        z_generator=range(64, 512+1, 64),
        x_generator=range(2, 25),
        averaging_generator=range(1),
        simulation=partial(grid_single_type, grid_size_x=5, link_reliability=1.0, log_messages=True),
        kwargs={"grid_size_y": "y", "fw_size": "x"}
):
    # vliv velikosti firmwaru na celkovy cas konvergence + vliv velikosti site na dobu konvergence
    setup_rng()
    stats = []
    for z in z_generator:
        stats_err = []
        for x in x_generator:
            reruns = []
            for rerun in averaging_generator:
                print(f'fwsize: {z} rr{rerun}, i{x}')
                kw = {"z": z, "x": x}
                kww = {k: kw[v] for k, v in kwargs.items()}
                y = simulation(**kww)
                reruns.append(extract_stats(y))

            stats_err.append((5 * x, reruns))
        stats.append((z, stats_err))

    make_graph("Grid size vs time",
               [(f"fwsize: {err}", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Network Size",
               "Time needed", "grid_longx5_size_vs_time_vs_fwsize.png", True)

def square_grid_fwsize_vs_time():
    # vliv velikosti firmwaru na celkovy cas konvergence
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        for fwsize in range(256, 4096, 256):
            reruns = []
            for rerun in range(1):
                print(f'err: {err} rr{rerun}, i{fwsize}')
                x = grid_single_type(
                    grid_size_x=10,
                    grid_size_y=10,
                    fw_size=fwsize,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((err, stats_err))

    make_graph("FWSize vs time",
               [(f"err: {err}%", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "FWsize",
               "Time needed", "square_grid_fwsize_vs_time.png", True)


def seed_corner_vs_center():
    # vliv pozice seed nodu v mrizce | vysledek - cim vetsi mrizka, tim signifikantnejsi rozdil (25x25 - 9%) |
    # asi nemuzeme rict, ze aby byl update rychlejsi, tak je lepsi mit seed ve stredu - simulator nezohlednuje dobu potrebnou k prenosu ruznych zprav - announce vs data
    # ani nemuzeme vzit pocet poslanych zprav kazdeho druhu a udelat vazenou sumu - nevime, kolik data messages bylo posilano paralelne
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        poses = [grid_single_type, grid_single_type_center]
        for pos in poses:
            reruns = []
            for rerun in range(5):
                print(f'err: {err} rr{rerun}, i{pos}')
                x = pos(
                    grid_size_x=25,
                    grid_size_y=25,
                    fw_size=64,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((poses.index(pos), reruns))
        stats.append((err, stats_err))

    make_graph("Seed position vs time",
               [(f"err: {err}%", [num_devs for num_devs, stats_err in stats[0][1]], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Seed position",
               "Time needed", "seed_corner_vs_center.png", True)


def square_grid_msg_overhead():
    # overhead protokolu vuci datum
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        for fwsize in range(512, 2048 + 1, 512):
            reruns = []
            for rerun in range(5):
                print(f'err: {err} rr{rerun}, i{fwsize}')
                x = grid_single_type(
                    grid_size_x=10,
                    grid_size_y=10,
                    fw_size=fwsize,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((err, stats_err))

    # stats[0][1][0][1][0].sent_by_type_len()

    # z_label: List[Tuple[str, Any]] = []

    make_graph(
        "FWSize vs time",
       [
           (
               f"(ann+req)/data%",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           (len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2])+y.sent_by_type_len(RequestMessage)) / y.sent_by_type_len(DataMessage)
                           for y in stats_y
                       ]
                   ) for grid_y, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual data / expected data",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(DataMessage) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual requests / expected requests",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(RequestMessage) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual announces v2 / expected announces v2",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2]) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ],
       "FWsize",
       "Ratio",
       "overhead.png",
       True
       )

def square_grid_msg_overhead_vs_err():
    # influence of error on messages overhead
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        for fwsize in range(512, 2048 + 1, 512):
            reruns = []
            for rerun in range(5):
                print(f'err: {err} rr{rerun}, i{fwsize}')
                x = grid_single_type(
                    grid_size_x=10,
                    grid_size_y=10,
                    fw_size=fwsize,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((err, stats_err))

    # stats[0][1][0][1][0].sent_by_type_len()

    # z_label: List[Tuple[str, Any]] = []

    make_graph(
        "FWSize vs time",
       [
           (
               f"(ann+req)/data%",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           (len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2])+y.sent_by_type_len(RequestMessage)) / y.sent_by_type_len(DataMessage)
                           for y in stats_y
                       ]
                   ) for grid_y, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual data / expected data",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(DataMessage) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual requests / expected requests",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(RequestMessage) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"actual announces v2 / expected announces v2",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2]) / ((10*10 - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ],
       "FWsize",
       "Ratio",
       "overhead.png",
       True
       )


def radial_grid_msg_overhead_vs_err():
    # influence of error on messages overhead
    setup_rng()
    stats = []
    for err in range(1):
        stats_err = []
        for fwsize in range(512, 2048 + 1, 512):
            reruns = []
            for rerun in range(5):
                print(f'err: {err} rr{rerun}, i{fwsize}')
                x = grid_single_type_center_radial(
                    radius=6,
                    fw_size=fwsize,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((err, stats_err))

    make_graph(
        "Protocol Overhead",
       [
           (
               f"(A + R) / D",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           (
                               len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2]) +
                               y.sent_by_type_len(RequestMessage)
                           ) / y.sent_by_type_len(DataMessage)
                           for y in stats_y
                       ]
                   ) for grid_y, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"Sent(D) / Expected(D)",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(DataMessage) / ((y.num_devices - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"Sent(R) / Expected(R)",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           y.sent_by_type_len(RequestMessage) / ((y.num_devices - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ] + [
           (
               f"Sent(A) / Expected(A)",
               [num_devs for num_devs, stats_err in stats[0][1]],
               [
                   avg(
                       [
                           len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if x.dsc.version == 2]) / ((y.num_devices - 1) * fwsize)
                           for y in stats_y
                       ]
                   ) for fwsize, stats_y in stats_err
               ]
           ) for err, stats_err in stats
       ],
       "Number of Chunks",
       "Ratio",
       "radial-overhead.pdf",
       True
       )


def radial_grid_msg_overhead_vs_err_real():
    # influence of error on messages overhead
    setup_rng()
    stats = []
    for err in [4]:
        stats_err = []
        for fwsize in range(128, 1024 + 1, 128):
            reruns = []
            for rerun in range(5):
                print(f'err: {err} rr{rerun}, i{fwsize}')
                x = grid_single_type_center_radial(
                    radius=5,
                    fw_size=fwsize,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((fwsize, reruns))
        stats.append((err, stats_err))

    make_graph(
        "Protocol Overhead",
        [
            (
                f"(A + R) / D",
                [num_devs for num_devs, stats_err in stats[0][1]],
                [
                    avg(
                        [
                            (
                                    len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if
                                         x.dsc.version == 2]) +
                                    y.sent_by_type_len(RequestMessage)
                            ) / y.sent_by_type_len(DataMessage)
                            for y in stats_y
                        ]
                    ) for grid_y, stats_y in stats_err
                ]
            ) for err, stats_err in stats
        ] + [
            (
                f"Sent(D) / Expected(D)",
                [num_devs for num_devs, stats_err in stats[0][1]],
                [
                    avg(
                        [
                            y.sent_by_type_len(DataMessage) / ((y.num_devices - 1) * fwsize)
                            for y in stats_y
                        ]
                    ) for fwsize, stats_y in stats_err
                ]
            ) for err, stats_err in stats
        ] + [
            (
                f"Sent(R) / Expected(R)",
                [num_devs for num_devs, stats_err in stats[0][1]],
                [
                    avg(
                        [
                            y.sent_by_type_len(RequestMessage) / ((y.num_devices - 1) * fwsize)
                            for y in stats_y
                        ]
                    ) for fwsize, stats_y in stats_err
                ]
            ) for err, stats_err in stats
        ] + [
            (
                f"Sent(A) / Expected(A)",
                [num_devs for num_devs, stats_err in stats[0][1]],
                [
                    avg(
                        [
                            len([x for x in y.sent_messages_by_type.get(AnnounceMessage.__name__) if
                                 x.dsc.version == 2]) / ((y.num_devices - 1) * fwsize)
                            for y in stats_y
                        ]
                    ) for fwsize, stats_y in stats_err
                ]
            ) for err, stats_err in stats
        ],
        "Number of Chunks",
        "Ratio",
        "radial-overhead-realerr.pdf",
        True
    )


def barbell_path_length_vs_time_vs_err():
    # network size influence on convergence time
    setup_rng()
    stats = []
    path_lengths = list(range(1, 18 + 1))
    for err in range(10):
        stats_err = []
        for path_len in path_lengths:
            reruns = []
            for rerun in range(15):
                print(f'err: {err} path_len: {path_len} rerun: {rerun}')
                x = barbell_single_type(
                    bell_size=6,
                    path_length=path_len,
                    fw_size=32,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True,
                )
                reruns.append(extract_stats(x))

            stats_err.append((reruns[0].num_devices, reruns))
        stats.append((err, stats_err))

    make_graph("Path Length and Convergence Time",
               [(f"loss: {err} %", path_lengths, [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Path Length",
               "Convergence Time", "barbell_path_length_vs_time_vs_errrrun10.pdf", True)


def ellipse_eccentricity():
    # influence of network planar shape on convergence time
    setup_rng()
    stats = []
    s = 5
    grids = list(zip([2 ** i for i in range(s)], [2 ** i for i in range(2*(s-1), -1, -1)]))
    for err in range(1):
        stats_err = []
        for i, (grid_x, grid_y) in zip([x + y - 2 for x, y in grids], grids):
            reruns = []
            for rerun in range(10):
                print(f'err: {err} grid_y: {grid_y} rerun: {rerun}')
                x = grid_single_type(
                    grid_size_x=grid_x,
                    grid_size_y=grid_y,
                    fw_size=32,
                    link_reliability=1.0 - (err / 100.0),
                    log_messages=True
                )
                reruns.append(extract_stats(x))

            stats_err.append((i, reruns))
        stats.append((err, stats_err))

    make_graph("Grid (Width + Height) and Convergence Time",
               [(f"msg loss: {err}%", [x + y - 2 for x, y in grids], [avg([y.runtime for y in stats_y]) for grid_y, stats_y in stats_err]) for err, stats_err in stats], "Grid Width + Height",
               "Convergence Time", "ellipse_eccentricity.pdf", True)


grid_radial_size_vs_time_vs_seed_position()
grid_radial_size_vs_time_vs_err()
radial_fwsize_vs_time_vs_radius()
radial_grid_msg_overhead_vs_err()
ellipse_eccentricity()
barbell_path_length_vs_time_vs_err()
multi_grid_radial_size_vs_time()
multi_grid_radial_size_vs_time_single_component()


# grid_long_size_vs_time_vs_err()
# grid_long_size_vs_time_vs_grid_x()
# grid_radial_size_vs_time()

# radial_grid_msg_overhead_vs_err_real()

