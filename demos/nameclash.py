from explotest import explore, Mode


class Foo:
    x = 1
    y = 2


class Bar:
    x = 3
    y = 4


@explore(mode=Mode.RECONSTRUCT)
def myfunc(foo, bar, bar2):
    return


myfunc(Foo(), Bar(), Bar())
