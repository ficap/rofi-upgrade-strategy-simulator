import asyncio
import sys
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





async def client(devices: List[Device]):
    sin = await connect_stdin()
    await cmd_handler(sin, devices)

