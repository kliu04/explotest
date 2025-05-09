import inspect
import pprint


def explore(func):
    def wrapper(*args, **kwargs):
        # doesn't seem to work well...
        # pprint.pprint(inspect.getouterframes(inspect.currentframe()))
        result = func(*args, **kwargs)
        return result

    return wrapper
