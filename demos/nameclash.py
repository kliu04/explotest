from explotest import explore, Mode


class Foo:
    x = 1
    y = 2


class Bar:
    x = 1
    y = 2


@explore(mode=Mode.RECONSTRUCT)
def myfunc(foo, bar):
    return


myfunc(Foo(), Bar())
