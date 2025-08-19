from pathlib import Path

from explotest import explore


@explore
def write_to_file(data: str) -> None:
    """
    Writes `data` to a file called to file.txt

    file.txt must exist, if it does not, a `FileNotFoundError` is raised.
    """
    target = Path(r"file.txt")
    if not target.is_file():
        raise FileNotFoundError(
            "No such file called file.txt in current working directory. Try creating the file."
        )

    with open("file.txt", "a") as f:
        f.write(data)


def target() -> str:
    """
    Returns file.txt as a string, with every character incremented by 1 in its value.
    """
    target = Path(r"file.txt")
    if not target.is_file():
        raise FileNotFoundError(
            "No such file called file.txt in current working directory. Try creating the file."
        )

    with open("file.txt", "r") as f:
        return "".join([chr(ord(c) + 1) for c in f.read()])


if __name__ == "__main__":
    write_to_file("meow")
    write_to_file("meow2")
    print(target())
