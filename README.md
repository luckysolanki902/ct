# ct — stealth screenshot sender / receiver

Two-mode terminal app:
- **Sender (1)**: silently watches the cursor. The instant it touches the **bottom-left corner**, it grabs a screenshot (no shutter / flash / UI), uploads it to S3, deletes the temp file, then ignores the corner for a **2-second cooldown** before it can fire again. Any error is logged — never crashes. Stop with `Ctrl+C`.
- **Receiver (2)**: polls S3 and downloads **everything** under the project's prefix — including files uploaded while it wasn't running — through the configured CloudFront CDN into `downloads/<File's Readable Date>/<readable time>.png`. Keeps running and grabs new ones as they appear. Stop with `Ctrl+C`.
- **Clean (3)**: deletes **every** object under the project's S3 prefix (`ct/...`). Other projects in the same bucket are untouched. Asks for `yes` confirmation before deleting.

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
python main.py        # prompts for 1 / 2 / 3
python main.py 1      # sender
python main.py 2      # receiver (asks: live-only?)
python main.py 2 --live   # receiver, skip existing backlog, only new uploads
python main.py 3      # clean S3 (under ct/ prefix only)
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
```

All uploads/downloads/cleans are scoped to `S3_PREFIX`, so other projects in the same bucket are never touched.

## Files

- [main.py](main.py) — mode picker
- [sender.py](sender.py) — corner-touch screenshot + S3 upload loop
- [receiver.py](receiver.py) — S3 poll + CDN download loop (downloads everything)
- [cleaner.py](cleaner.py) — deletes all objects under the project's S3 prefix
- [common.py](common.py) — env loading, logging, S3 client
