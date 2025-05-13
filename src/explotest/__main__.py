import os
import sys

from .system_provider import SystemProvider  # type: ignore


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)
    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(os.path.dirname(target))
    sys.path.insert(0, script_dir)

    SystemProvider(target)


if __name__ == "__main__":
    main()
