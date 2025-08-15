from typing import Any


lst: list[Any] = []


def add_elem(data: Any) -> None:
    lst.append(data)


def target(i) -> Any:  #
    return lst[i]


def main():
    add_elem("hello")
    add_elem("world")
    print(target(-1))


if __name__ == "__main__":
    main()
