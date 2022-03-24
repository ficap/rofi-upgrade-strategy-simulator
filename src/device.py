import asyncio

from asyncio.queues import Queue
from random import choices, randint, shuffle
from typing import Dict, Optional, Union, Sequence

from firmware import Firmware
from messages import AnnounceMsg, RequestMsg, DataMsg


def random_entry(seq: Sequence):
    return seq[randint(0, len(seq) - 1)]


class Device:
    def __init__(self, idx: int, dev_type: int, input_queue: Queue, connections: Dict[int, Queue],
                 running_firmware: Firmware, new_firmware: Optional[Firmware] = None, timeout: float = 0.25,
                 msg_success_rate: float = 1.0):
        self.idx: int = idx
        self.dev_type: int = dev_type
        self.input_queue: Queue = input_queue
        self.connections: Dict[int, Queue] = connections
        self.running_firmware: Firmware = running_firmware
        self.new_firmware: Optional[Firmware] = new_firmware
        self.timeout: float = timeout
        self.msg_success_rate: float = msg_success_rate
        self.cache = []

        # self.conn_perms = list(itertools.permutations(self.connections.values()))
        self.shuffled_conns = list(self.connections.values())

        self.timeouts: int = 0
        self.killed: bool = False

    def __str__(self):
        return f"idx: {self.idx:02d}, upgrading: {self.is_upgrading():d}, type: {self.dev_type}, " \
               f"in_queue: {self.input_queue.qsize():02d}, " \
               f"running_fw: {self.running_firmware}, new_fw: {self.new_firmware}"

    async def send_message(self, queue: Queue, msg: Union[AnnounceMsg, RequestMsg, DataMsg]):
        # print(f"Sending {msg}")
        await queue.put(msg)

    async def receive_message(self):
        while True:
            msg = await asyncio.wait_for(self.input_queue.get(), self.timeout)
            success = choices([True, False], [self.msg_success_rate, 1.0 - self.msg_success_rate], k=1)[0]

            if success:
                return msg

    def is_upgrading(self) -> bool:
        return self.new_firmware is not None

    async def _handle_announce_msg(self, msg: AnnounceMsg) -> None:
        if msg.fw_type != self.dev_type:
            # todo: if chunk is not in cache
            await self.send_message(self.connections[msg.from_node],
                                    RequestMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id))
            return

        if msg.version > self.running_firmware.version:
            if not self.is_upgrading():  # we have full older version and might be in process of upgrading to lower version than this message already
                # print(f"{self.idx}: beginning upgrade to version {msg.version}")
                # todo: instead of line below use stg. like _begin_upgrade(1, msg.version, msg.num_of_chunks)
                self.new_firmware = Firmware(1, msg.version, msg.num_of_chunks * [None])  # todo: handle firmware types
                await self.send_message(self.connections[msg.from_node], RequestMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id))

            elif self.is_upgrading() and self.new_firmware.version == msg.version:  # we're already in transition to this new version
                if not self.new_firmware.is_chunk_present(msg.chunk_id):  # we don't have this chunk yet
                    await self.send_message(self.connections[msg.from_node], RequestMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id))

                else:  # we already have this chunk do we want to continue in announcing this chunk?
                    pass  # not yet it might not be needed to generate additional traffic

            elif self.is_upgrading() and msg.version > self.new_firmware.version:
                pass  # do we want to abort upgrade and start upgrade to higher version?

            else:  # we're already upgrading to higher version than this message announces
                pass

        else:  # we have higher or the same version as in msg already
            pass  # we won't downgrade or pass the message further

    async def _handle_request_msg(self, msg: RequestMsg) -> None:
        # should total number of chunks of firmware be sent as well to prevent useless data packets transfer?
        if msg.version == self.running_firmware.version and msg.fw_type == self.running_firmware.fw_type:
            if self.running_firmware.is_chunk_present(msg.chunk_id):
                await self.send_message(self.connections[msg.from_node],
                                        DataMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id,
                                                self.running_firmware.data_size, 1,
                                                self.running_firmware.data[msg.chunk_id]))
            else:  # it's not a valid request
                pass

        # should total number of chunks of firmware be sent as well to prevent useless data packets transfer?
        elif self.is_upgrading() and msg.version == self.new_firmware.version and msg.fw_type == self.new_firmware.fw_type:
            if self.new_firmware.is_chunk_present(msg.chunk_id):
                await self.send_message(self.connections[msg.from_node],
                                        DataMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id,
                                                self.new_firmware.data_size, 1,
                                                self.new_firmware.data[msg.chunk_id]))

            else:  # we don't have requested data
                if self.new_firmware.is_valid_chunk_id(msg.chunk_id):
                    # request chunk from random neighbor
                    await self.send_message(random_entry(list(self.connections.values())),
                                            RequestMsg(self.idx, msg.fw_type, msg.version, msg.chunk_id))

        else:  # todo: request data it might be different type of firmware
            pass

    async def _handle_data_msg(self, msg: DataMsg) -> None:
        if msg.fw_type != self.dev_type:
            # todo: if not in cache
            self.cache.append(msg)
            # todo: announce
            return

        if self.is_upgrading():
            if msg.version == self.new_firmware.version and msg.fw_type == self.new_firmware.fw_type:  # todo: check num_of_chunks
                if self.new_firmware.is_valid_chunk_id(msg.chunk_id) and not self.new_firmware.is_chunk_present(msg.chunk_id):
                    self.new_firmware.data[msg.chunk_id] = msg.data

                    shuffle(self.shuffled_conns)
                    for q in self.shuffled_conns:
                        await self.send_message(q,
                                                AnnounceMsg(self.idx, msg.fw_type, msg.version,
                                                            msg.chunk_id, msg.num_of_chunks))

                    if self.new_firmware.is_complete():
                        # we have all data
                        # print(f"{self.idx}: successfully upgraded to version {msg.version}")
                        self.running_firmware = self.new_firmware
                        self.new_firmware = None

            else:  # we already have this chunk. did we requested it at all??
                # we may check if the data equals if we are upgrading but we might not be (not implemented yet)
                pass

        else:
            pass  # for now we ignore other data messages

    async def _handle_timeout(self):
        if self.is_upgrading() and not self.new_firmware.is_complete():
            # for now let's request first missing chunk from random neighbor
            missing_chunks = self.new_firmware.get_missing_chunks()
            req_chunk_id = random_entry(missing_chunks)

            self.timeouts += 1

            # print(f"{self.idx} timeout {self.timeouts}")
            await self.send_message(random_entry(list(self.connections.values())),
                                    RequestMsg(self.idx, self.dev_type, self.new_firmware.version, req_chunk_id))

    async def loop(self):
        for _, queue in self.connections.items():
            # I have whole firmware and I announce random part of it
            await self.send_message(
                queue,
                AnnounceMsg(self.idx, self.running_firmware.fw_type, self.running_firmware.version,
                            randint(0, self.running_firmware.data_size - 1), self.running_firmware.data_size)
            )

        while not self.killed:
            try:
                msg = await self.receive_message()
                if isinstance(msg, AnnounceMsg):
                    await self._handle_announce_msg(msg)

                elif isinstance(msg, RequestMsg):
                    await self._handle_request_msg(msg)

                elif isinstance(msg, DataMsg):
                    await self._handle_data_msg(msg)

            except asyncio.TimeoutError:
                await self._handle_timeout()

    def kill(self):
        self.killed = True
