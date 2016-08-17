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
