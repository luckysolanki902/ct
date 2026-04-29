"""Syncer: upload local sync.txt so sender-side sync consumers overwrite their copy."""
import os
import traceback

from common import (
    setup_logger,
    get_s3_client,
    AWS_S3_BUCKET_NAME,
    SYNC_OBJECT_KEY,
)

log = setup_logger("sync")


def run():
    local_path = os.path.join(os.path.dirname(__file__), "sync.txt")
    if not os.path.exists(local_path):
        log.error("sync.txt not found at %s", local_path)
        return

    if not AWS_S3_BUCKET_NAME:
        log.error("AWS_S3_BUCKET_NAME not set.")
        return

    try:
        with open(local_path, "rb") as f:
            body = f.read()
    except Exception as e:
        log.error("Failed to read sync.txt: %s", e)
        return

    try:
        s3 = get_s3_client()
    except Exception as e:
        log.error("S3 client init failed: %s", e)
        return

    try:
        s3.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=SYNC_OBJECT_KEY,
            Body=body,
            ContentType="text/plain; charset=utf-8",
        )
        log.info(
            "Uploaded sync file (%d bytes) -> s3://%s/%s",
            len(body),
            AWS_S3_BUCKET_NAME,
            SYNC_OBJECT_KEY,
        )
    except Exception as e:
        log.error("Upload failed: %s\n%s", e, traceback.format_exc())


if __name__ == "__main__":
    run()
