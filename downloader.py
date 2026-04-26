import os
import socket

import requests


class Downloader:
    def __init__(self, tmp_dir="tmp"):
        self.tmp_dir = tmp_dir
        os.makedirs(tmp_dir, exist_ok=True)

    def download(self, url, filename):
        local_path = os.path.join(self.tmp_dir, filename)

        if os.path.exists(local_path):
            os.remove(local_path)

        try:
            r = requests.get(
                url,
                stream=True,
                timeout=(5, 60),  # 🔑 CRITICAL
                headers={"User-Agent": "Mozilla/5.0"}
            )
            r.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        except (requests.RequestException, socket.timeout) as e:
            if os.path.exists(local_path):
                os.remove(local_path)
            raise RuntimeError(f"Download failed: {e}")

        file_hash = self.file_sha256(local_path)
        return local_path, file_hash

    def rename_if_duplicate(self, filename, file_hash, existing_hashes):
        if file_hash not in existing_hashes:
            return filename

        base, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            counter += 1
            if new_name not in existing_hashes:
                return new_name

    @staticmethod
    def file_sha256(path):
        import hashlib
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
