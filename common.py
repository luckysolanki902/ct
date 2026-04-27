"""Shared config + S3 client."""
import os
import logging
from dotenv import load_dotenv
import boto3
from botocore.config import Config

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "").rstrip("/")
S3_PREFIX = os.getenv("S3_PREFIX", "ct/screenshots/")
if not S3_PREFIX.endswith("/"):
    S3_PREFIX += "/"


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                                         datefmt="%H:%M:%S"))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)
    return logger


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=Config(retries={"max_attempts": 5, "mode": "standard"},
                      connect_timeout=10, read_timeout=30),
    )
