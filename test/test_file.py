from another_test_file import bar  # type: ignore
import numpy as np
import ast

# from explotest.explore import explore  # type: ignore
import sys


def baz(string: str, n: int):
    if n == 0:
        return len(string)
    else:
        return baz(string + "a", n - 1)


# @explore
def foo(x: int, y: int) -> int:
    x += y
    y += x
    # x += int(sys.argv[1])
    return x + y + bar()


def main():
    if False:
        print("never")
    else:
        x = baz("Hello World!", 7)
        print(foo(x, 2))


if __name__ == "__main__":
    main()
