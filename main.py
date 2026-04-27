"""Entry point: prompt for 1 (sender), 2 (receiver), or 3 (clean) and run.

Receiver flags:
  --live / -l   Skip existing files in S3, only download new uploads from now on.
"""
import sys


def main():
    args = [a.strip() for a in sys.argv[1:]]
    flags = {a.lower() for a in args if a.startswith("-")}
    positionals = [a for a in args if not a.startswith("-")]

    live_only = "--live" in flags or "-l" in flags

    arg = positionals[0].lower() if positionals else ""
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
        run()
    elif arg == "2":
        from receiver import run
        if not positionals and not flags:
            try:
                ans = input("Live-only (skip existing backlog)? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            live_only = ans in ("y", "yes")
        run(live_only=live_only)
    else:
        from cleaner import run
        run()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
