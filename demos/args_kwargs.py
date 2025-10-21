import explotest


@explotest.explore(mode="p")
def foo1(x, y, z, *args, bar, baz, **kwargs):
    print(x, y, z, args, bar, baz, kwargs)


@explotest.explore(mode="p")
def foo2(x, y, z=0):
    print(x, y, z)


@explotest.explore(mode="p")
def bar(x, y, /, z, *, bar):
    print(x, y, z, bar)


bar(1, 2, 3, bar=4)


foo1(1, 2, 3, 4, 5, baz=6, bar=7, kwarg1=True, kwarg2=False)
foo2(1, 2, 3)
foo2(1, 2)
bar(1, 2, 3, bar=4)
