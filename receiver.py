"""Receiver: poll S3 for new screenshots, download via CDN into today's folder with readable timestamp filenames."""
import os
import time
import traceback
from datetime import datetime
from urllib.parse import quote

import requests

from common import (
    setup_logger, get_s3_client,
    AWS_S3_BUCKET_NAME, S3_PREFIX, CDN_BASE_URL,
)

log = setup_logger("receiver")

POLL_INTERVAL = 5.0           # seconds between S3 list checks
CDN_CONNECT_TIMEOUT = 4        # seconds to establish CDN connection
CDN_READ_TIMEOUT = 8           # seconds to read CDN response
S3_DOWNLOAD_TIMEOUT = 30       # seconds for direct S3 download
DOWNLOAD_ROOT = "downloads"


def _folder_for(dt: datetime) -> str:
    # e.g. "April 27, 2026"
    folder_name = dt.strftime("%B %d, %Y").replace(" 0", " ")
    path = os.path.join(DOWNLOAD_ROOT, folder_name)
    os.makedirs(path, exist_ok=True)
    return path


def _readable_time(dt: datetime) -> str:
    # e.g. "10 30 45 AM"
    s = dt.strftime("%I %M %S %p")
    if s.startswith("0"):
        s = s[1:]
    return s


def _list_keys(s3):
    keys = []
    token = None
    while True:
        kwargs = {"Bucket": AWS_S3_BUCKET_NAME, "Prefix": S3_PREFIX}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []) or []:
            k = obj["Key"]
            if k.endswith("/"):
                continue
            keys.append((k, obj.get("LastModified")))
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def _cdn_url(key: str) -> str:
    if not CDN_BASE_URL:
        return ""
    return f"{CDN_BASE_URL}/{quote(key)}"


def _download_via_cdn(key: str, dest_path: str) -> bool:
    url = _cdn_url(key)
    if not url:
        return False
    try:
        log.info("CDN GET %s", url)
        # Non-streaming: small PNGs, and the (connect, read) timeout actually
        # bounds the whole transfer this way. Streaming would let body bytes
        # hang indefinitely after headers arrive.
        r = requests.get(url, timeout=(CDN_CONNECT_TIMEOUT, CDN_READ_TIMEOUT))
        if r.status_code != 200:
            log.warning("CDN returned HTTP %d for %s", r.status_code, key)
            return False
        tmp = dest_path + ".part"
        with open(tmp, "wb") as f:
            f.write(r.content)
        os.replace(tmp, dest_path)
        return True
    except Exception as e:
        log.warning("CDN download failed for %s: %s", key, e)
        try:
            if os.path.exists(dest_path + ".part"):
                os.remove(dest_path + ".part")
        except Exception:
            pass
        return False


def _download_via_s3(s3, key: str, dest_path: str) -> bool:
    try:
        log.info("S3 GET s3://%s/%s", AWS_S3_BUCKET_NAME, key)
        tmp = dest_path + ".part"
        s3.download_file(AWS_S3_BUCKET_NAME, key, tmp)
        os.replace(tmp, dest_path)
        return True
    except Exception as e:
        log.error("S3 download failed for %s: %s", key, e)
        try:
            if os.path.exists(dest_path + ".part"):
                os.remove(dest_path + ".part")
        except Exception:
            pass
        return False


def _download(s3, key: str, dest_path: str) -> bool:
    # Try CDN first; fall back to direct S3 if CDN fails (e.g. distribution
    # not configured for this prefix, cache miss + permission, etc).
    if _download_via_cdn(key, dest_path):
        return True
    log.info("Falling back to direct S3 for %s", key)
    return _download_via_s3(s3, key, dest_path)


def _unique_path(folder: str, base: str, ext: str) -> str:
    candidate = os.path.join(folder, f"{base}{ext}")
    i = 2
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base} ({i}){ext}")
        i += 1
    return candidate


def run():
    log.info("Receiver started. Polling s3://%s/%s every %.1fs. Ctrl+C to stop.",
             AWS_S3_BUCKET_NAME, S3_PREFIX, POLL_INTERVAL)
    seen = set()
    s3 = None

    # Wait until S3 client is ready, but DO NOT baseline existing objects:
    # we want to download everything that's already there too.
    while s3 is None:
        try:
            s3 = get_s3_client()
        except KeyboardInterrupt:
            log.info("Stopping receiver (Ctrl+C).")
            return
        except Exception as e:
            log.error("S3 client init failed, retrying: %s", e)
            s3 = None
            time.sleep(POLL_INTERVAL)

    while True:
        try:
            keys = _list_keys(s3)
            # Sort by LastModified so older arrivals are downloaded first
            keys.sort(key=lambda kv: kv[1] or datetime.min)
            new_items = [kv for kv in keys if kv[0] not in seen]
            if new_items:
                log.info("Found %d new file(s).", len(new_items))
            for key, last_modified in new_items:
                ts = last_modified if isinstance(last_modified, datetime) else datetime.now()
                # Convert to local time for folder + filename
                try:
                    ts_local = ts.astimezone()
                except Exception:
                    ts_local = ts
                folder = _folder_for(ts_local)
                base = _readable_time(ts_local)
                ext = os.path.splitext(key)[1] or ".png"
                dest = _unique_path(folder, base, ext)
                log.info("Downloading %s -> %s", key, dest)
                if _download(s3, key, dest):
                    log.info("Saved %s", dest)
                    seen.add(key)
                else:
                    log.error("All download methods failed for %s (will retry)", key)
                # if download failed, leave it un-seen so we retry next cycle
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log.info("Stopping receiver (Ctrl+C).")
            return
        except Exception as e:
            log.error("Poll loop error: %s\n%s", e, traceback.format_exc())
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
