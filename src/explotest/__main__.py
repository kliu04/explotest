import os
import runpy
import sys

def main():

    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    target_folder = os.path.dirname(target)
    sys.argv = sys.argv[1:]

    script_dir = os.path.abspath(target_folder)
    sys.path.insert(0, script_dir)

    runpy.run_path(os.path.abspath(target), run_name="__main__")


if __name__ == "__main__":
    main()
