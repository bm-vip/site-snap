import csv
import os

class Config:
    def __init__(self):
        self.start_urls = self.start_urls = self._load_urls()

        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "172.17.0.2:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "insurance-resources")
        self.minio_secure = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")

        if not self.minio_access_key or not self.minio_secret_key:
            raise Exception("MINIO_ACCESS_KEY or MINIO_SECRET_KEY is missing")

    @staticmethod
    def _load_urls():
        csv_path = os.path.join(os.path.dirname(__file__), "siteUrls.csv")
        urls = []

        with open(csv_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    url = row[0].strip()
                    if url:
                        urls.append(url)

        return urls
