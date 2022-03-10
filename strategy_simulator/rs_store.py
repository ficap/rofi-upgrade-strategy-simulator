from collections import OrderedDict
from typing import Optional, Hashable, Set

from .clock import ClockView


class RequestStore:
    class MPair:
        __slots__ = ('time', 'devices')

        def __init__(self, time: int = 0, devices: Optional[Set[int]] = None):
            self.time = time
            self.devices = devices or set()

    def __init__(self, clock: ClockView, timeout: int, max_capacity: Optional[int] = None):
        self._clock = clock
        self._timeout = timeout
        self.max_capacity: Optional[int] = max_capacity
        self._d = OrderedDict()
        self._max_used_size = 0

    def get_requesters(self, dsc: Hashable) -> Set[int]:
        entry = self._d.get(dsc)
        if entry is None or entry.time < self._clock.now:
            self._clean_in_flight_requests(dsc)
            return set()

        self._d.move_to_end(dsc)
        return set(entry.devices)  # return copy since it is usually manipulated by other methods inside cycles

    def is_request_in_flight_for_anybody(self, dsc: Hashable) -> bool:
        return self._clean_in_flight_requests(dsc)

    def mark_request_in_flight_for(self, dsc: Hashable, for_id: int, in_flight: bool = True):
        if not in_flight:
            entry = self._d.get(dsc)
            if entry is None:
                return
            if for_id in entry.devices:
                entry.devices.remove(for_id)
            self._clean_in_flight_requests(dsc)
            return

        # if it is an expired record remove it to clear expired device entries
        self._clean_in_flight_requests(dsc)
        if len(self._d) == self.max_capacity and dsc not in self._d:
            self._d.popitem(last=False)
        entry = self._d.setdefault(dsc, RequestStore.MPair())
        self._d.move_to_end(dsc)
        self._max_used_size = max(self._max_used_size, len(self._d))
        # todo: reset its timeout or simply pass?
        # let's reset timeout
        entry.time = self._clock.now + self._timeout
        entry.devices.add(for_id)

    def _clean_in_flight_requests(self, dsc: Hashable) -> bool:
        """Does the cleanup on the key and returns true if the record remains present thus is valid"""
        entry = self._d.get(dsc)
        if entry is None:
            return False

        if entry.time < self._clock.now or len(entry.devices) == 0:
            del self._d[dsc]
            return False

        self._d.move_to_end(dsc)
        return True


class RecentlySeenStore:
    def __init__(self, clock: ClockView, timeout: int, max_capacity: Optional[int] = None):
        self._clock = clock
        self._timeout = timeout
        self.max_capacity: Optional[int] = max_capacity
        self._d = OrderedDict()
        self._max_used_size = 0

    def recently_seen(self, dsc: Hashable) -> bool:
        seen = dsc in self._d and self._d[dsc] >= self._clock.now
        if seen:
            self._d.move_to_end(dsc)
            return True
        return False

    def mark_recently_seen(self, dsc: Hashable):
        if dsc in self._d:
            self._d[dsc] = self._clock.now + self._timeout
            self._d.move_to_end(dsc)
            return

        self._remove_obsolete()
        if len(self._d) == self.max_capacity:
            self._d.popitem(last=False)

        self._d[dsc] = self._clock.now + self._timeout
        self._max_used_size = max(self._max_used_size, len(self._d))

    def _remove_obsolete(self):
        to_remove = []
        for k, v in self._d.items():
            if v < self._clock.now:
                to_remove.append(k)

        for k in to_remove:
            del self._d[k]
