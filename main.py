"""Entry point: prompt for 1 (sender), 2 (receiver), or 3 (clean) and run."""
import sys


def main():
    arg = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    aliases = {"clean": "3", "sender": "1", "receiver": "2"}
    arg = aliases.get(arg, arg)
    while arg not in ("1", "2", "3"):
        try:
            arg = input("Choose mode: 1 = sender, 2 = receiver, 3 = clean S3: ").strip().lower()
            arg = aliases.get(arg, arg)
        except (EOFError, KeyboardInterrupt):
            print()
            return
    if arg == "1":
        from sender import run
    elif arg == "2":
        from receiver import run
    else:
        from cleaner import run
    run()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
