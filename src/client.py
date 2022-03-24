import asyncio
import sys
import time
from typing import List, Callable

from device import Device


async def cmd_handler(sin, devices: List[Device]):
    data = None
    while data != b"exit\n":
        data = await sin.readline()

        if data == b"dump\n":
            for d in devices:
                print(d)


async def connect_stdin():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    # w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    # writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader  # , writer


async def watcher(period: float, devices: List[Device]):
    while True:
        msgs_in_queues = 0
        print("\033[H\033[J", end="")
        for d in devices:
            print(d)
            msgs_in_queues += d.input_queue.qsize()
        print(f"in queues: {msgs_in_queues}")
        print()

        await asyncio.sleep(period)


async def client(devices: List[Device]):
    sin = await connect_stdin()
    await cmd_handler(sin, devices)


async def all_devices_pass(devices: List[Device], period: float, predicate: Callable[[Device], bool]):
    start = time.time_ns()
    while True:
        fail = False
        # let's check all of them so that each run takes similar time
        for d in devices:
            if not predicate(d):
                fail = True

        if not fail:
            print("all devices passed")
            took = time.time_ns() - start
            took = took / 1000_000_000
            for device in devices:
                device.kill()
            print(f"it took {took} seconds")
            return True

        await asyncio.sleep(period)
