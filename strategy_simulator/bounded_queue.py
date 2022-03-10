from collections import deque
from typing import Optional, TypeVar, Deque, Tuple, Generic

from .clock import ClockView

T = TypeVar('T')


class BoundedQueue(Generic[T]):
    def __init__(self, clock: ClockView, maxlen: Optional[int] = None, debug: bool = False):
        self._q: Deque[T] = deque(maxlen=maxlen)
        self._clock: ClockView = clock
        self._debug: bool = debug
        self._max_used: int = 0

    def push(self, item: T) -> Optional[Tuple[int, T]]:
        if self._debug and self._q.maxlen and len(self._q) == self._q.maxlen:
            dropped = self.pop()
            self._q.append((self._clock.now, item))
            return dropped

        self._q.append((self._clock.now, item))
        self._max_used = max(self._max_used, len(self._q))

    def pop(self) -> Optional[T]:
        if len(self._q) > 0:
            ts, item = self._q[0]
            if ts < self._clock.now:
                return self._q.popleft()[1]
        return None

    def size(self) -> int:
        return len(self._q)
