import functools
import signal
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


def split_iterable(iterable, predicate=bool):
    """
    Yield sublists of `iterable`, split on elements that satisfy `predicate`.

    The elements that are split upon are discarded, and adjacent
    elements that split are condensed; an empty sublist will never
    be yielded.
    """
    section = []

    for element in iterable:
        if predicate(element):
            if section:
                yield section
                section = []
        else:
            section.append(element)

    if section:
        yield section


class cached_property(object):
    """
    Decorate a class method to turn it into a cached, read-only property.

    Works by dynamically adding a value member that overrides
    the `get` method.
    """

    def __init__(self, fget):
        for name in ('__name__', '__module__', '__doc__'):
            setattr(self, name, getattr(fget, name))
        self._fget = fget

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.__dict__[self._fget.__name__] = self._fget(instance)
        return value


class Timeout(object):
    """
    http://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish/22348885#22348885
    """
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type_, value, traceback):
        signal.alarm(0)
