from functools import wraps


def with_lock(lock):
    def wrapper(fn):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            lock.acquire()
            
            try:
                response = fn(*args, **kwargs)
            finally:
                lock.release()
            return response
        return wrapped_fn
    return wrapper
