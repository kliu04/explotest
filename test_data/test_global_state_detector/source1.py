from typing import Any


lst: list[Any] = []


def add_elem(data: Any) -> None:
    lst.append(data)


def target() -> Any: # 
    return lst[-1]


def main():
    add_elem("hello")
    add_elem("world")
    print(target())


if __name__ == "__main__":
    main()
