from test2 import bar


@explore
def foo(x: int, y: int) -> int:
    x += y
    y += x
    return x + y + bar()


def main():
    print(foo(1, 2))


if __name__ == "__main__":
    main()
