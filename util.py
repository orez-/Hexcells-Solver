import functools
import sys
import time


def timeit(msg):
    def decorator(fn):
        @functools.wraps(fn)
        def anon(*args, **kwargs):
            print(msg, end='')
            sys.stdout.flush()
            t = time.time()
            result = fn(*args, **kwargs)
            print(' - {:.1f}s'.format(time.time() - t))
            return result
        return anon
    return decorator


def color_diff(color1, color2):
    """
    Given two rgb tuples, find their difference.
    """
    return sum(abs(a - b) for a, b in zip(color1, color2))


def partition_if(iterable, predicate=lambda x: x):
    truthy = []
    falsey = []
    for value in iterable:
        if predicate(value):
            truthy.append(value)
        else:
            falsey.append(value)
    return truthy, falsey
