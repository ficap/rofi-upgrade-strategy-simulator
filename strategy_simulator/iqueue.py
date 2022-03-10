from random import choices
from typing import Any, List, Optional, Tuple

from .clock import ClockView
from .bounded_queue import BoundedQueue


class WriteQueue:
    def __init__(self, write_queue, writer_id: Any, clock: ClockView, write_reliability: float = 1.0,
                 debug: bool = False):
        self._write_queue = write_queue
        self._clock: ClockView = clock
        self.writer_id: Any = writer_id
        self.write_reliability: float = write_reliability
        self.debug: bool = debug
        self._lost_messages: List[Any] = []
        self._sent_messages: List[Any] = []
        self._overflowed_messages: List[Tuple[int, Any]] = []

    def write(self, o: Any):
        success = choices([True, False], [self.write_reliability, 1.0 - self.write_reliability], k=1)[0]

        if self.debug:
            if success:
                self._sent_messages.append(o)
            else:
                self._lost_messages.append(o)

        if success:
            overflow = self._write_queue.push((self.writer_id, o))
            if self.debug and overflow is not None:
                self._overflowed_messages.append(overflow)


class ReadQueue:
    def __init__(self, clock: ClockView, debug: bool = False, maxlen: Optional[int] = None):
        self._clock: ClockView = clock
        self.debug: bool = debug
        self._q: BoundedQueue = BoundedQueue(self._clock, maxlen=maxlen)
        self._received_messages: List[Any] = []

    def write_queue_for_writer(self, writer_id: Any, write_reliability: float = 1.0,
                               debug: Optional[bool] = None) -> WriteQueue:
        debug = debug or self.debug
        return WriteQueue(self._q, writer_id, self._clock, write_reliability, debug)

    def try_read(self) -> Optional[Tuple[Any, Any]]:
        m = self._q.pop()
        if self.debug and m is not None:
            self._received_messages.append(m)
        return m
