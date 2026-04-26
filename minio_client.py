import os
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error


class MinioClient:
    def __init__(self, endpoint, access_key, secret_key, bucket, secure):
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            http_client=None  # allow internal retries
        )

        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def upload(self, site_url, local_path, filename):
        domain = urlparse(site_url).netloc
        object_name = f"{domain}/{filename}"

        counter = 1
        original = filename
        while self.object_exists(object_name):
            name, ext = os.path.splitext(original)
            filename = f"{name}_{counter}{ext}"
            object_name = f"{domain}/{filename}"
            counter += 1

        try:
            self.client.fput_object(
                self.bucket,
                object_name,
                local_path,
            )
        except S3Error as e:
            raise RuntimeError(f"MinIO upload failed: {e}")

        return object_name

    def object_exists(self, object_name):
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except:
            return False
