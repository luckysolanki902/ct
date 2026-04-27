"""Entry point: prompt for 1 (sender) or 2 (clean) and run."""
import sys


def main():
    args = [a.strip() for a in sys.argv[1:]]
    positionals = [a for a in args if not a.startswith("-")]

    arg = positionals[0].lower() if positionals else ""
    aliases = {"clean": "2", "sender": "1"}
    arg = aliases.get(arg, arg)
    while arg not in ("1", "2"):
        try:
            arg = input("Choose mode: 1 = sender, 2 = clean S3: ").strip().lower()
            arg = aliases.get(arg, arg)
        except (EOFError, KeyboardInterrupt):
            print()
            return

    if arg == "1":
        from sender import run
        run()
    else:
        from cleaner import run
        run()


if __name__ == "__main__":
    main()
