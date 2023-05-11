import dataclasses as dcs
from math import ceil
from typing import Dict, Optional, Any, List

from .firmware import Firmware
from .metrics import counted
from .messages import ChunkDescriptor, AnyMessage, DataMessage, AnnounceMessage, RequestMessage, Proto, RawData, FWType, \
    Version
from .iqueue import WriteQueue, ReadQueue
from .clock import ClockView
from .rs_store import RecentlySeenStore, RequestStore

DeviceId = int
DeviceType = int


class OngoingUpgrade:
    def __init__(self, fw_type: FWType, version: Version, proto: Proto):
        self.fw_type: FWType = fw_type
        self.version: Version = version
        self.proto: Proto = proto
        self.last_progress: int = -1
        self.candidate_firmware: Firmware = Firmware(fw_type, version, [None] * proto.chunks)


class Device:
    CHUNK_SIZE: int = 1

    # limitation: all neighbors share the same queue for the target device thus we're not able to model each link's
    # reliability alone thus reliability should, from this PoV, be a property of the device
    def __init__(self, dev_id: DeviceId, dev_type: DeviceType, input_queue: ReadQueue,
                 neighbors: Dict[DeviceId, WriteQueue], running_firmware: Firmware, clock: ClockView,
                 diff_announces_seen_store=None, in_flight_requests_store=None, datas_seen_store=None):
        self.dev_id: DeviceId = dev_id
        self.dev_type: DeviceType = dev_type

        self._clock = clock
        self._stats: Dict[Any, Any] = {}  # temporary solution, to be moved to simulator
        self._input_queue: ReadQueue = input_queue
        self.neighbors: Dict[DeviceId, WriteQueue] = neighbors

        self.running_firmware: Firmware = running_firmware

        self._ongoing_upgrade: Optional[OngoingUpgrade] = None
        self._current_message: Optional[AnyMessage] = None  # todo: remove this hacky way

        self.periodic_announce: int = 100
        self._last_periodic_announce: int = -self.periodic_announce
        # todo: if self.in_flight_timeout >= self.progress_timeout then spontaneous requests do not work
        #  either check this condition or make self.upgrade_process_timeout_handler
        #  use unrestricted impl of _request_message_for that would send all requests without limits/restrictions
        self.progress_timeout: int = 100  # todo: pass from argument
        # self._last_progress resides inside self._ongoing_upgrade

        self._diff_announces_seen_store = diff_announces_seen_store or RecentlySeenStore(self._clock, timeout=self.periodic_announce//2, max_capacity=None)
        self._in_flight_requests_store = in_flight_requests_store or RequestStore(self._clock, timeout=self.progress_timeout//2, max_capacity=None)
        self._datas_seen_store = datas_seen_store or RecentlySeenStore(self._clock, timeout=self.progress_timeout//2, max_capacity=None)

    @property
    def upgrading(self) -> bool:
        """The device is being upgraded/is in a process of upgrade of its firmware"""
        return self._ongoing_upgrade is not None

    def on_before_message(self, m: AnyMessage) -> bool:
        if m.proto.chunk_size != Device.CHUNK_SIZE:
            return True

        self._current_message = m  # todo: remove this hacky way

        if isinstance(m, DataMessage):
            if m.dsc.fw_type != self.dev_type:
                if self._datas_seen_store.recently_seen(m.dsc):
                    return True
                self._datas_seen_store.mark_recently_seen(m.dsc)
            self._try_satisfy_foreign_requests(m.dsc, m.data)
            if m.dsc.fw_type != self.dev_type:
                return True

        if m.dsc.fw_type == self.dev_type:
            return False

        if isinstance(m, AnnounceMessage):
            if not self._diff_announces_seen_store.recently_seen(m.dsc):
                self._diff_announces_seen_store.mark_recently_seen(m.dsc)
                self._announce_chunk(m.dsc, exclude_devices=[m.proto.from_device])
            return True

        if isinstance(m, RequestMessage):
            self._request_chunk_for_device(m.proto.from_device, m.dsc)
            return True

        return False

    def on_announce_message(self, m: AnnounceMessage):
        if m.dsc.fw_type != self.dev_type:  # this is never true, only here to know message's invariants
            return
        if m.dsc.version <= self.running_firmware.version:
            return

        if not self.upgrading:
            self._init_upgrade(m.dsc.fw_type, m.dsc.version, m.proto)

        if m.dsc.version != self._ongoing_upgrade.version:
            # unless ongoing upgrade is completed we don't accept newer versions
            return

        if self._ongoing_upgrade.candidate_firmware.is_chunk_present(m.dsc.chunk_id):
            return

        self._request_chunk_from_device(m.proto.from_device, m.dsc)
        # todo: do we want to keep the below line here or not??
        self._ongoing_upgrade.last_progress = self._clock.now

    def on_request_message(self, m: RequestMessage):
        if m.dsc.fw_type != self.dev_type:
            # this won't happen anytime - handled in on_before_message
            return

        if m.dsc.version == self.running_firmware.version:
            if not self.running_firmware.is_chunk_present(m.dsc.chunk_id):  # todo: replace with chunkid validity test
                return
            self._send_data(m.dsc, m.proto.from_device, self.running_firmware.data[m.dsc.chunk_id])  # todo: unspecialize from adaptation for chunksize==1
            self._announce_next_chunk_to_device(m.dsc, m.proto.from_device, self.running_firmware)
            return

        if not self.upgrading:
            # todo: in case we allow devices to not upgrade themselves we have to at least make them pass messages
            # todo: if so all other parts of code/protocol need to be checked and adjusted if needed
            return

        if m.dsc.version != self._ongoing_upgrade.version:
            return

        if not self._ongoing_upgrade.candidate_firmware.is_chunk_present(m.dsc.chunk_id):
            if not self._ongoing_upgrade.candidate_firmware.is_valid_chunk_id(m.dsc.chunk_id):  # todo: move above
                return

            # as it is the same version, type and chunk_id this device will also eventually need so how about ignoring
            # this request, sink it, and continue with native process of getting the chunk for this device in standard
            # order, that is as a response to announce message
            # the device that originally sent this request as a ??result of timeout??
            # (is timeout the only way how the request got here??) will keep timeouting until it
            # receives this chunk
            self._request_chunk_for_device(m.proto.from_device, m.dsc)
            # we are interested in the chunk too, but we certainly don't want to bcst the request twice -> accomplished
            # by internal functionality of request_chunk_for_device
            self._request_chunk_for_device(self.dev_id, m.dsc)
            # todo: ???
            # todo: should we ask for the chunk? Let's try not to, it might be unnecessary
            # todo: after all it might be necessary because of spontaneous requests??
            return

        self._send_data(m.dsc, m.proto.from_device, self._ongoing_upgrade.candidate_firmware.data[m.dsc.chunk_id])  # todo: unspecialize from adaptation for chunksize==1
        self._announce_next_chunk_to_device(m.dsc, m.proto.from_device, self._ongoing_upgrade.candidate_firmware)

    def on_data_message(self, m: DataMessage):
        if m.dsc.fw_type != self.dev_type:  # this won't happen anytime - handled in on_before_message
            return

        if not self.upgrading:
            return

        if m.dsc.version != self._ongoing_upgrade.version or \
                not self._ongoing_upgrade.candidate_firmware.is_valid_chunk_id(m.dsc.chunk_id) or \
                self._ongoing_upgrade.candidate_firmware.is_chunk_present(m.dsc.chunk_id):
            return

        self._ongoing_upgrade.candidate_firmware.data[m.dsc.chunk_id] = m.data
        # todo: maybe abstract it to some ongoing_upgrade method??
        self._ongoing_upgrade.last_progress = self._clock.now

        self._in_flight_requests_store.mark_request_in_flight_for(m.dsc, self.dev_id, in_flight=False)

        self._announce_chunk(m.dsc, exclude_devices=[m.proto.from_device])

        if self._ongoing_upgrade.candidate_firmware.is_complete():
            self._commit_upgrade()

    def upgrade_process_timeout_handler(self):
        if self.upgrading and self._clock.now - self._ongoing_upgrade.last_progress > self.progress_timeout:
            u = self._ongoing_upgrade
            # todo: do we need to emit spontaneous request? doesn't it suffice to wait as all devices emit announces?
            #  maybe it doesn't because devices with incomplete ongoing_upgrade
            #  does not emit announces of their available ongoing_upgrade's chunks
            #  and we only announce the first chunk periodically
            self._request_chunk_for_device(
                self.dev_id,
                ChunkDescriptor(u.fw_type, u.version, u.candidate_firmware.get_first_missing_chunk()),
                proto=self._ongoing_upgrade.proto
            )

            self._ongoing_upgrade.last_progress = self._clock.now
            return

    def periodic_running_firmware_announcer(self):
        if self._clock.now - self._last_periodic_announce > self.periodic_announce:
            r = self.running_firmware
            proto = Proto(0, Device.CHUNK_SIZE, ceil(r.data_size / Device.CHUNK_SIZE), r.data_size)

            self._announce_chunk(ChunkDescriptor(r.fw_type, r.version, 0), proto=proto)
            self._last_periodic_announce = self._clock.now

    def tick(self):
        # if self.dev_type == FW_TYPE_B:
        self.periodic_running_firmware_announcer()
        self.upgrade_process_timeout_handler()

        msg = self._try_receive_message()
        if msg is None:
            return

        consumed = self.on_before_message(msg)
        if consumed:
            self._current_message = None  # todo: remove this hacky way
            return

        if isinstance(msg, AnnounceMessage):
            self.on_announce_message(msg)

        elif isinstance(msg, RequestMessage):
            self.on_request_message(msg)

        elif isinstance(msg, DataMessage):
            self.on_data_message(msg)

        self._current_message = None

    def _init_upgrade(self, fw_type: FWType, version: Version, proto: Proto):
        self._ongoing_upgrade = OngoingUpgrade(fw_type, version, proto)

    def _commit_upgrade(self):
        self.running_firmware = self._ongoing_upgrade.candidate_firmware
        self._ongoing_upgrade = None

    def _announce_chunk(self, dsc: ChunkDescriptor, exclude_devices: Optional[List[DeviceId]] = None, proto: Optional[Proto] = None):
        """
        Sends announce message announcing a chunk described by dsc ChunkDescriptor
        to all immediate neighbors excluding specified ones
        Does not have any inner guard, thus must be called with care to avoid network congestion
        """
        proto = proto or self._current_message.proto  # todo: remove this somehow hacky way
        m = AnnounceMessage(proto, dsc)  # todo: use correct values
        self._broadcast_message(m, exclude_devices=exclude_devices)

    def _announce_chunk_to_device(self, dsc: ChunkDescriptor, device: DeviceId):
        m = AnnounceMessage(self._current_message.proto, dsc)  # todo: use correct values
        self._send_message(device, m)

    def _announce_next_chunk_to_device(self, current_dsc: ChunkDescriptor, device: DeviceId, firmware: Firmware):
        """
        Announces next available chunk of the firmware to the device
        If there is no next chunk available then does nothing
        Note: next available chunk might not necessarily be the immediately following one
        """
        next_chunk_id = firmware.get_next_chunk_present(current_dsc.chunk_id)
        if next_chunk_id:
            self._announce_chunk_to_device(dcs.replace(current_dsc, chunk_id=next_chunk_id), device)

    def _request_chunk_from_device(self, from_device: DeviceId, dsc: ChunkDescriptor):
        in_flight = self._in_flight_requests_store.is_request_in_flight_for_anybody(dsc)
        self._in_flight_requests_store.mark_request_in_flight_for(dsc, self.dev_id)

        if not in_flight:
            req = RequestMessage(self._current_message.proto, dsc)  # todo: use correct values
            self._send_message(from_device, req)

    def _request_chunk_for_device(self, for_device: DeviceId, dsc: ChunkDescriptor, proto: Optional[Proto] = None):  # todo: possibly merge with _request_chunk
        proto = proto or self._current_message.proto

        in_flight = self._in_flight_requests_store.is_request_in_flight_for_anybody(dsc)
        self._in_flight_requests_store.mark_request_in_flight_for(dsc, for_device)

        if not in_flight:
            req = RequestMessage(proto, dsc)
            self._broadcast_message(req, exclude_devices=[for_device])

    def _send_data(self, dsc: ChunkDescriptor, device: DeviceId, data: RawData):
        m = DataMessage(self._current_message.proto, dsc, data)  # todo: use correct values
        self._send_message(device, m)

    def _try_satisfy_foreign_requests(self, dsc: ChunkDescriptor, data: RawData):
        reqs = self._in_flight_requests_store.get_requesters(dsc)

        msg = DataMessage(self._current_message.proto, dsc, data)  # todo: use correct values
        for dst in reqs-{self.dev_id}:  # todo: fix this
            self._in_flight_requests_store.mark_request_in_flight_for(dsc, dst, in_flight=False)
            self._send_message(dst, msg)

    @counted
    def _send_message(self, device_id: DeviceId, msg: AnyMessage):
        queue = self.neighbors[device_id]
        queue.write(msg)

    def _broadcast_message(self, m: AnyMessage, exclude_devices: Optional[List[DeviceId]]):
        """Sends given message to all immediate neighbors excluding ones specified in exclude_devices"""
        exclude_devices = exclude_devices or []

        for device_id in self.neighbors:
            if device_id in exclude_devices:
                continue
            self._send_message(device_id, m)

    def _try_receive_message(self):
        m = self._input_queue.try_read()
        if m is None:
            return None

        dev_id, m = m
        proto = dcs.replace(m.proto, from_device=dev_id)
        m = dcs.replace(m, proto=proto)
        return m
