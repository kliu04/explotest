import explotest


@explotest.explore(mode="p")
def foo1(x, y, z, *args, bar, baz, **kwargs):
    print(x, y, z, args, bar, baz, kwargs)


@explotest.explore(mode="p")
def foo2(x, y, z=0):
    print(x, y, z)


foo1(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
foo2(1, 2, 3)
foo2(1, 2)
