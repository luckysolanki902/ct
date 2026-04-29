# ct — screenshot sender + sync + corner typer

Modes:
- **Sender (1)**: silently watches the cursor. The instant it touches the **bottom-left corner**, it grabs a screenshot (no shutter / flash / UI), uploads it to S3, deletes the temp file, then ignores the corner for a **2-second cooldown** before it can fire again. Any error is logged — never crashes. Stop with `Ctrl+C`.
- **Clean (2)**: deletes **every** object under the project's S3 prefix (`ct/...`). Other projects in the same bucket are untouched. Asks for `yes` confirmation before deleting.
- **Sync Push (3)**: uploads local `sync.txt` to `s3://<bucket>/ct/sync/sync.txt`. Any running sender instance auto-pulls and fully overwrites its local `sync.txt`.
- **Typer (4)**: move cursor to the **bottom-right corner** to start typing `sync.txt` via `pyautogui`. After 3 seconds of typing, move to bottom-right again to stop. Top-left pyautogui failsafe is disabled in this mode.

## Setup (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **macOS permissions**
> - **Screen Recording** — System Settings → Privacy & Security → Screen Recording → enable for Terminal/iTerm. Required for screenshots.
> - **Accessibility** — System Settings → Privacy & Security → Accessibility → enable for Terminal/iTerm. Required to read the cursor position.

## Run

```bash
python main.py        # prompts for 1 / 2 / 3 / 4
python main.py 1      # sender
python main.py 2      # clean S3 (under ct/ prefix only)
python main.py 3      # upload local sync.txt to sync object in S3
python main.py 4      # bottom-right trigger typing mode
```

## Config

`.env` (already created):

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_S3_BUCKET_NAME=testingmaddy2
CDN_BASE_URL=https://d3efr8i3xj2spn.cloudfront.net
S3_PREFIX=ct/screenshots/
SYNC_OBJECT_KEY=ct/sync/sync.txt
SYNC_POLL_SECONDS=1.0
```

All uploads/downloads/cleans are scoped to `S3_PREFIX`, so other projects in the same bucket are never touched.

## Files

- [main.py](main.py) — mode picker
- [sender.py](sender.py) — corner-touch screenshot + S3 upload loop
- [cleaner.py](cleaner.py) — deletes all objects under the project's S3 prefix
- [syncer.py](syncer.py) — uploads local `sync.txt` to S3 sync object
- [typer.py](typer.py) — bottom-right trigger pyautogui typing mode
- [common.py](common.py) — env loading, logging, S3 client
