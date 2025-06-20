from typing import Self

from explotest import explore, Mode


f = open("file.txt")


@explore(mode=Mode.RECONSTRUCT)
def foo(x):
    print(x)


foo(f)
