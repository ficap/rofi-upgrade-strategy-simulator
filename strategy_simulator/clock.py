class Clock:
    def __init__(self, time_init: int = 0):
        self._time = time_init

    @property
    def now(self):
        return self._time

    def tick(self):
        self._time += 1

    def clock_view(self):
        return ClockView(self)


class ClockView:
    def __init__(self, clock: Clock):
        self._clock = clock

    @property
    def now(self):
        return self._clock.now
