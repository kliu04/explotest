from another_test_file import bar

# from explotest.explore import explore
import sys


# @explore
def foo(x: int, y: int) -> int:
    x += y
    y += x
    # x += int(sys.argv[1])
    return x + y + bar()


def main():
    print(foo(1, 2))


if __name__ == "__main__":
    main()
