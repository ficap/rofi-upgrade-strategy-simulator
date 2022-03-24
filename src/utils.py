import time


def duration(function):
    start = time.time_ns()
    result = function()
    took = time.time_ns() - start
    took = took / 1000_000_000
    
    return took, result

