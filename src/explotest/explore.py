def explore(func):
    def wrapper(*args, **kwargs):
        # ignore these
        # print(inspect.getsource(func))
        # print(inspect.getfile(func))
        # print(inspect.getmodule(func))
        # print(inspect.getsourcefile(func))
        # print(inspect.getsource(inspect.getmodule(func)))
        result = func(*args, **kwargs)
        return result

    return wrapper
