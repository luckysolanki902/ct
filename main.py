"""Entry point: prompt for mode and run."""
import sys


def main():
    args = [a.strip() for a in sys.argv[1:]]
    positionals = [a for a in args if not a.startswith("-")]

    arg = positionals[0].lower() if positionals else ""
    aliases = {
        "sender": "1",
        "clean": "2",
        "sync": "3",
        "type": "4",
        "typer": "4",
    }
    arg = aliases.get(arg, arg)
    while arg not in ("1", "2", "3", "4"):
        try:
            arg = input(
                "Choose mode: 1 = sender, 2 = clean S3, 3 = sync.txt push, 4 = type sync.txt: "
            ).strip().lower()
            arg = aliases.get(arg, arg)
        except (EOFError, KeyboardInterrupt):
            print()
            return

    if arg == "1":
        from sender import run
        run()
    elif arg == "2":
        from cleaner import run
        run()
    elif arg == "3":
        from syncer import run
        run()
    else:
        from typer import run
        run()


if __name__ == "__main__":
    main()
