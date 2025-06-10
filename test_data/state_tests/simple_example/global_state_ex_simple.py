from typing import Any

from src.explotest import explore

lst: list[Any] = []


def add_elem(data: Any) -> None:
    lst.append(data)


@explore
def get_elem_at_end() -> Any:
    return lst[-1]


def main():
    add_elem("hello")
    add_elem("world")
    print(get_elem_at_end())


if __name__ == "__main__":
    main()
