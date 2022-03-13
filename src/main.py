import asyncio
import random
import itertools
from dataclasses import dataclass
from asyncio import Queue
import logging


messages_sent = 0
MSG_SUCCESS_RATE=.99

net = [
    [2],
    [2, 4],
    [0, 1, 3, 4],
    [2, 6],
    [1, 2, 5, 6],
    [4],
    [3, 4]
]


@dataclass
class AnnounceMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int
    num_of_chunks: int


@dataclass
class RequestMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int


@dataclass
class DataMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int
    num_of_chunks: int
    chunk_length: int
    data: int


async def send_message(queue, msg):
    success = random.choices([True, False], [MSG_SUCCESS_RATE, 1.0 - MSG_SUCCESS_RATE], k=1)[0]
    if success:
        print(f"Sending {msg}")
        await queue.put(msg)
        global messages_sent
        messages_sent += 1
        print(f"messages sent: {messages_sent}")
    else:
        print(f"messages failed: {messages_sent}")


firmware_length = 10

async def blah(idx: int, fw_type: int, ver: int, connections: list, queues):
    timeouts = 0
    data = list(range(firmware_length))
    new_data = list()
    new_ver = ver

    queue = queues[idx]

    for i in connections:
        await send_message(queues[i], AnnounceMsg(idx, fw_type, ver, random.randint(0, firmware_length-1), firmware_length))  # I have whole firmware and I announce random part of it

    while True:
        try:
            msg = await asyncio.wait_for(queue.get(), 5)
            if isinstance(msg, AnnounceMsg):
                if msg.version > ver:
                    if new_ver < msg.version:  # we have full older version and might be in process of upgrading to lower version than this message already
                        print(f"{idx}: beginning upgrade to version {msg.version}")
                        new_ver = msg.version
                        new_data = msg.num_of_chunks * [None]
                        await send_message(queues[msg.from_node], RequestMsg(idx, msg.fw_type, msg.version, msg.chunk_id))

                    elif new_ver == msg.version:  # we're already in transition to this new version
                        if new_data[msg.chunk_id] == None:  # we don't have this chunk yet
                            #print("req")
                            await send_message(queues[msg.from_node], RequestMsg(idx, msg.fw_type, msg.version, msg.chunk_id))
                        else:  # we already have this chunk do we want to pass this event to another nodes??
                            pass  # not yet it might not be needed to generate additional traffic

                    else:  # new_ver > msg.version  we're upgrading to greater version than this message
                        pass  # I have greater version so I won't announce older one

                else:  # we have higher or same version as in msg already
                    pass  # we won't downgrade or pass the message further

            elif isinstance(msg, RequestMsg):
                if msg.version == ver:
                    if msg.chunk_id < len(data):
                        #print("dat")
                        await send_message(queues[msg.from_node], DataMsg(idx, msg.fw_type, msg.version, msg.chunk_id, len(data), 1, data[msg.chunk_id]))
                    else:  # it's not valid request
                        pass

                elif msg.version == new_ver:
                    if msg.chunk_id < len(new_data):
                        if new_data[msg.chunk_id] != None:
                            #print("dat")
                            await send_message(queues[msg.from_node], DataMsg(idx, msg.fw_type, msg.version, msg.chunk_id, len(new_data), 1, new_data[msg.chunk_id]))
                        else:  # we don't have requested data
                            await send_message(queues[random.randint(0, len(connections) - 1)], RequestMsg(idx, msg.fw_type, msg.version, msg.chunk_id))
                    else:  # it's not valid request
                        pass

            elif isinstance(msg, DataMsg):
                if msg.version == new_ver:
                    if new_data[msg.chunk_id] == None:  # it seems that we're in transition to this new version let's accept data
                        new_data[msg.chunk_id] = msg.data

                        for i in list(itertools.permutations(connections))[random.randint(0, len(connections)-1)]:
                            await asyncio.sleep(random.uniform(0, .1))
                            #print("ann")
                            await send_message(queues[i], AnnounceMsg(idx, msg.fw_type, msg.version, msg.chunk_id, len(new_data)))

                        if not any([d == None for d in new_data]):
                            # we have all data
                            print(f"{idx}: successfully upgraded to version {msg.version}")
                            data = new_data
                            ver = new_ver

                    else:  # we already have this chunk. did we requested it at all??
                        # we may check if the data equals if we are upgrading but we might not be (not implemented yet)
                        pass

                else:
                    pass  # for now we ignore other data messages

        except asyncio.TimeoutError:
            if new_ver > ver and any([d == None for d in new_data]):  # we're in transition process and missing some chunks
                # for now let's request first missing chunk from random neighbor
                req_chunk_id = next(filter(lambda x: x[1], enumerate([d == None for d in new_data])))[0]
                
                timeouts += 1
                print(f"{idx} timeout {timeouts}")
                await send_message(queues[random.randint(0, len(connections) - 1)], RequestMsg(idx, fw_type, new_ver, req_chunk_id))

# TODO: implement handling of different fw_types
# TODO: implement requesting of unannounced missing chunks (packet drop)
# TODO: use NetworkX

BUFFER_SIZE = 1

async def main():
    queues = [Queue() for _ in range(len(net))]
    coros = [blah(0, 1, 2, net[0], queues)] + [blah(i, 1, 1, net[i], queues) for i in range(1, len(net))]

    # for now we explicitly announce all chunks
    init_seeder_idx = 0
    connections = net[init_seeder_idx]  # node 0 is initial seeder
    
    messages_sent = 0
    await asyncio.gather(*coros)


asyncio.run(main())
