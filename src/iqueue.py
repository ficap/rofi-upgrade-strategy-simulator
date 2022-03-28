# class Queue:
#     def __init__(self):
#         self.queue = []
# 
#     def get(self):
#         if len(self.queue) > 0:
#             return self.queue.pop(0)
# 
#         return None
# 
#     def put(self, item):
#         self.queue.append(item)
# 
#     def size(self):
#         return len(self.queue)
# 
#     def __sizeof__(self):
#         return len(self.queue)
from queue import PriorityQueue
from typing import Optional


class Entry:
    def __init__(self, prio, item):
        self.prio = prio
        self.item = item

    def __gt__(self, i):
        return self.prio > i

    def __lt__(self, i):
        return self.prio < i

    def __eq__(self, i):
        return self.prio == i

    def __str__(self):
        return f"{self.prio} - {self.item}"


class Queue:
    def __init__(self):
        self.queue = PriorityQueue()

    def pop(self, time: Optional[int] = None):
        if not self.queue.empty():
            if time is not None and self.queue.queue[0].prio <= time:
                return self.queue.get_nowait().item

        return None

    def put(self, priority, item):
        self.queue.put_nowait(Entry(priority, item))

    def size(self):
        return self.queue.qsize()

    def __sizeof__(self):
        return self.queue.qsize()

    def peek(self):
        if not self.queue.empty():
            return self.queue.queue[0].item

        return None

    def __str__(self):
        for i in self.queue.queue:
            return str(i)