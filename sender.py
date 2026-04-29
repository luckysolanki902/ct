"""Sender: watch cursor, capture stealth screenshot on bottom-left trigger, upload to S3."""
import os
import time
import uuid
import tempfile
import traceback
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from common import (
    setup_logger, get_s3_client,
    AWS_S3_BUCKET_NAME, S3_PREFIX,
    SYNC_OBJECT_KEY, SYNC_POLL_SECONDS,
)

log = setup_logger("sender")

# How close to the bottom-left corner counts as "in the corner".
# Wider than 3px because the macOS Dock + hot-corner gestures often keep
# the cursor a few px away from the true edge.
CORNER_THRESHOLD_PX = 25
# Cooldown after a capture: ignore further triggers for this many seconds.
COOLDOWN_SECONDS = 2.0
# Polling interval
POLL_INTERVAL = 0.05


def _get_screen_size():
    import pyautogui
    w, h = pyautogui.size()
    return int(w), int(h)


def _get_cursor_pos():
    import pyautogui
    p = pyautogui.position()
    return int(p.x), int(p.y)


def _capture_screenshot(path: str):
    """Silent screenshot using mss (no shutter, no flash, no UI)."""
    import mss
    with mss.mss() as sct:
        # monitor 0 = all monitors combined; 1 = primary
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        img = sct.grab(monitor)
        # Save as PNG via mss tools (faster, no Pillow needed)
        import mss.tools as mtools
        mtools.to_png(img.rgb, img.size, output=path)


def _upload(s3, local_path: str) -> str:
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y-%m-%d")
    time_part = now.strftime("%H%M%S-%f")
    key = f"{S3_PREFIX}{date_part}/{time_part}-{uuid.uuid4().hex[:8]}.png"
    s3.upload_file(
        local_path, AWS_S3_BUCKET_NAME, key,
        ExtraArgs={"ContentType": "image/png"},
    )
    return key


def _sync_local_file_from_s3(s3, last_etag: str | None) -> str | None:
    """If sync object changed, overwrite local sync.txt and return the latest etag."""
    try:
        head = s3.head_object(Bucket=AWS_S3_BUCKET_NAME, Key=SYNC_OBJECT_KEY)
    except ClientError as e:
        code = (e.response or {}).get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey", "NotFound"):
            return last_etag
        raise

    etag = (head.get("ETag") or "").strip('"')
    if etag and etag == last_etag:
        return last_etag

    resp = s3.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=SYNC_OBJECT_KEY)
    body = resp["Body"].read()

    local_path = os.path.join(os.path.dirname(__file__), "sync.txt")
    tmp_path = f"{local_path}.tmp"
    with open(tmp_path, "wb") as f:
        f.write(body)
    os.replace(tmp_path, local_path)
    log.info("sync.txt updated from s3://%s/%s (%d bytes).", AWS_S3_BUCKET_NAME, SYNC_OBJECT_KEY, len(body))
    return etag or last_etag


def run():
    try:
        screen_w, screen_h = _get_screen_size()
    except Exception as e:
        log.error("Failed to read screen size: %s", e)
        return

    log.info(
        "Sender started. Screen=%dx%d. Touch bottom-LEFT corner to capture (then %.1fs cooldown). Ctrl+C to stop.",
        screen_w,
        screen_h,
        COOLDOWN_SECONDS,
    )

    s3 = None
    try:
        s3 = get_s3_client()
    except Exception as e:
        log.error("Failed to init S3 client (will retry on demand): %s", e)

    cooldown_until = 0.0  # monotonic timestamp
    next_sync_check = 0.0
    last_sync_etag = None

    while True:
        try:
            try:
                x, y = _get_cursor_pos()
            except Exception as e:
                log.warning("Cursor read failed: %s", e)
                time.sleep(POLL_INTERVAL)
                continue

            in_corner = (x <= CORNER_THRESHOLD_PX) and \
                        (y >= screen_h - 1 - CORNER_THRESHOLD_PX)

            now = time.monotonic()
            if in_corner and now >= cooldown_until:
                log.info("Trigger at (%d,%d). Capturing...", x, y)
                cooldown_until = now + COOLDOWN_SECONDS
                _trigger(s3)

            if now >= next_sync_check:
                next_sync_check = now + max(SYNC_POLL_SECONDS, POLL_INTERVAL)
                try:
                    client = s3 if s3 is not None else get_s3_client()
                    if s3 is None:
                        s3 = client
                    last_sync_etag = _sync_local_file_from_s3(client, last_sync_etag)
                except Exception as e:
                    log.warning("sync poll failed: %s", e)

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log.info("Stopping sender (Ctrl+C).")
            return
        except Exception as e:
            log.error("Loop error: %s\n%s", e, traceback.format_exc())
            time.sleep(0.5)


def _trigger(s3):
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix="cap_", suffix=".png")
        os.close(fd)
        _capture_screenshot(tmp_path)
        size = os.path.getsize(tmp_path)
        log.info("Captured screenshot (%d bytes). Uploading...", size)

        # lazy s3 init if it failed earlier
        client = s3
        if client is None:
            try:
                client = get_s3_client()
            except Exception as e:
                log.error("S3 client init failed: %s", e)
                return

        key = _upload(client, tmp_path)
        log.info("Uploaded -> s3://%s/%s", AWS_S3_BUCKET_NAME, key)
    except Exception as e:
        log.error("Capture/upload failed: %s\n%s", e, traceback.format_exc())
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                log.warning("Failed to delete temp file %s: %s", tmp_path, e)


if __name__ == "__main__":
    run()
