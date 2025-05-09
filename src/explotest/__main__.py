import runpy
import sys
import trace
import coverage

ignore_modules = [
    # "_bootstrap_external",
    # "_bootstrap",
    # "explotest",
    # "_virtualenv",
    # "provider",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m explotest <filename>")
        sys.exit(1)

    target = sys.argv[1]
    sys.argv = sys.argv[1:]

    # runpy.run_path(target, run_name="__main__")

    tracer = trace.Trace(ignoremods=ignore_modules)

    with open(target, "r") as f:
        tracer.run(compile(f.read(), target, "exec"))


if __name__ == "__main__":
    main()
