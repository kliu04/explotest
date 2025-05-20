import functools
import inspect
import os

import dill


def is_primitive(x):
    return isinstance(x, (int, float, str, bool))


def explore(func):

    @functools.wraps(func)  # preserve docstrings, etc. of original fn
    def wrapper(*args, **kwargs):
        arg_spec = inspect.getfullargspec(func)
        arg_names = arg_spec.args
        import_statement = inspect.getfile(func).replace(os.sep, ".").replace(".py", "")

        with open("pickling_test.py", "w") as f:
            f.write(f"from {import_statement} import {func.__qualname__}\n")
            f.write("import dill\n")

            f.write("def test():\n")
            for arg_name, arg_value in zip(arg_names, args):
                if is_primitive(arg_value):
                    f.write(f"    {arg_name} = {arg_value}\n")
                else:
                    f.write(f"    {arg_name} = dill.loads({dill.dumps(arg_value)})\n")
            f.write("\n")
            f.write(f"    {func.__qualname__}({", ".join(arg_names)})")

        # TODO: convert to AST building representation
        # TODO: kwargs
        # TODO: command-line args

        # finally, call the subroutine-under-test
        result = func(*args, **kwargs)
        return result

    return wrapper
