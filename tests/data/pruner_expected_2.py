def foo(a: int) -> None:
    x = 42
    y = a
    z = 4
    w = 14
    y = z
    x = x + w
    l = 1

    # no else
    if y < 0:
        x = y

    print(x)
foo(1)
