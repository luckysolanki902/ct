# ct — stealth screenshot sender / receiver

Two-mode terminal app:
- **Sender (1)**: silently watches the cursor. When it sits in the **bottom-left corner for 2 seconds**, it grabs a screenshot (no shutter / flash / UI), uploads it to S3, deletes the temp file, then keeps watching. Any error is logged — never crashes. Stop with `Ctrl+C`.
- **Receiver (2)**: polls S3 for new files, downloads each new one through the configured CloudFront CDN into `downloads/<Today's Readable Date>/<readable time>.png`. Stop with `Ctrl+C`.

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
python main.py        # will prompt for 1 or 2
python main.py 1      # sender
python main.py 2      # receiver
```

## Config

`.env` (already created):

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_S3_BUCKET_NAME=testingmaddy2
CDN_BASE_URL=https://d3efr8i3xj2spn.cloudfront.net
S3_PREFIX=screenshots/
```

Receiver only downloads objects that appear **after** it starts (existing objects are baselined as already-seen).

## Files

- [main.py](main.py) — mode picker
- [sender.py](sender.py) — corner-dwell screenshot + S3 upload loop
- [receiver.py](receiver.py) — S3 poll + CDN download loop
- [common.py](common.py) — env loading, logging, S3 client
