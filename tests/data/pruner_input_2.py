def foo(a: int) -> None:
    x = 42
    y = a
    z = 4
    w = 14

    if y > 0:
        y = z
        x = x + w
        if y + z == w:
            k = 1
        elif False:
            z = 1
        else:
            l = 1
    elif True:
        m = 90
    else:
        print("hey")

    if y < 0:
        x = y

    print(x)


foo(1)
# foo(-1)
