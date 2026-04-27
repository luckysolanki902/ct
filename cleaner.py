"""Cleaner: delete EVERY object under S3_PREFIX in the configured bucket.

Hard-guard: refuses to run if S3_PREFIX is empty or "/" so we never wipe a whole
bucket by accident. Only objects under the project's own prefix are touched.
"""
import sys
import traceback

from common import (
    setup_logger, get_s3_client,
    AWS_S3_BUCKET_NAME, S3_PREFIX,
)

log = setup_logger("clean")

BATCH = 1000  # S3 delete_objects max


def _list_all_keys(s3):
    keys = []
    token = None
    while True:
        kwargs = {"Bucket": AWS_S3_BUCKET_NAME, "Prefix": S3_PREFIX}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []) or []:
            keys.append(obj["Key"])
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def run():
    if not S3_PREFIX or S3_PREFIX in ("/", ""):
        log.error("Refusing to clean: S3_PREFIX is empty. Set it in .env (e.g. ct/screenshots/).")
        return
    if not AWS_S3_BUCKET_NAME:
        log.error("AWS_S3_BUCKET_NAME not set.")
        return

    log.info("This will DELETE every object under s3://%s/%s", AWS_S3_BUCKET_NAME, S3_PREFIX)
    try:
        ans = input("Type 'yes' to confirm: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if ans != "yes":
        log.info("Aborted.")
        return

    try:
        s3 = get_s3_client()
    except Exception as e:
        log.error("S3 client init failed: %s", e)
        return

    try:
        keys = _list_all_keys(s3)
    except Exception as e:
        log.error("List failed: %s\n%s", e, traceback.format_exc())
        return

    if not keys:
        log.info("Nothing to delete under prefix '%s'.", S3_PREFIX)
        return

    log.info("Deleting %d object(s)...", len(keys))
    deleted = 0
    errors = 0
    for i in range(0, len(keys), BATCH):
        chunk = keys[i:i + BATCH]
        try:
            resp = s3.delete_objects(
                Bucket=AWS_S3_BUCKET_NAME,
                Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True},
            )
            errs = resp.get("Errors") or []
            errors += len(errs)
            for e in errs:
                log.error("Delete error: %s -> %s", e.get("Key"), e.get("Message"))
            deleted += len(chunk) - len(errs)
            log.info("Progress: %d/%d", min(i + len(chunk), len(keys)), len(keys))
        except Exception as e:
            errors += len(chunk)
            log.error("Batch delete failed: %s", e)

    log.info("Done. Deleted=%d, Errors=%d", deleted, errors)


if __name__ == "__main__":
    run()
