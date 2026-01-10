import functools
import time


def run_with_duration(attr_name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time
            setattr(self, attr_name, duration)
            return result

        return wrapper

    return decorator
