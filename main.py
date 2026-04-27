"""Entry point: prompt for 1 (sender) or 2 (receiver) and run."""
import sys


def main():
    arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    while arg not in ("1", "2"):
        try:
            arg = input("Choose mode: 1 = sender, 2 = receiver: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
    if arg == "1":
        from sender import run
        run()
    else:
        from receiver import run
        run()


if __name__ == "__main__":
    main()
