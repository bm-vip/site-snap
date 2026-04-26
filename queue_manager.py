import os
import threading
from queue import Queue as ThreadQueue, Empty
from urllib.parse import urlparse


class DownloadQueue:
    def __init__(self, downloader, uploader, state_manager, max_workers=5):
        self.downloader = downloader
        self.uploader = uploader
        self.state = state_manager
        self.max_workers = max_workers

        self._hash_lock = threading.Lock()
        self.existing_hashes = set(self.state.registry.values())

        self.thread_queue = ThreadQueue()
        self.processing = False
        self.workers = []

        self._load_queue_from_state()

    # ---------- State bootstrap ----------
    def _load_queue_from_state(self):
        queue_items_loaded = 0

        for url in self.state.queue_list:
            if not self.state.file_exists(url):
                site = self._find_site_for_pdf(url)
                if site:
                    self.thread_queue.put((url, site))
                    queue_items_loaded += 1

        if queue_items_loaded > 0:
            print(f"📥 Loaded {queue_items_loaded} items from previous state")

    def _find_site_for_pdf(self, pdf_url):
        pdf_domain = urlparse(pdf_url).netloc
        for visited_url in self.state.visited:
            if urlparse(visited_url).netloc == pdf_domain:
                return visited_url
        return None

    # ---------- Queue control ----------
    def add(self, url, site):
        if not self.state.file_exists(url):
            self.thread_queue.put((url, site))
            self.state.add_queue(url)
            print(f"📥 Added to queue: {url} (Queue size: {self.thread_queue.qsize()})")

    def run(self):
        items = []
        while not self.thread_queue.empty():
            items.append(self.thread_queue.get())

        if not items:
            print("ℹ️ Queue is empty")
            return

        self._process_items(items)

    def run_continuous(self):
        self.processing = True
        print("🔄 Starting continuous download processing...")

        self.workers = []
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._continuous_worker,
                name=f"DownloadWorker-{i}",
                daemon=False
            )
            worker.start()
            self.workers.append(worker)

    def stop_continuous(self):
        self.processing = False
        self.thread_queue.join()
        print("🛑 Continuous download processing stopped")

        for worker in self.workers:
            worker.join()

    def _continuous_worker(self):
        while self.processing or not self.thread_queue.empty():
            try:
                task = self.thread_queue.get(timeout=2)
                self.worker(task)
                self.thread_queue.task_done()
            except Empty:
                continue

    # ---------- Worker logic ----------
    def worker(self, task):
        url, site = task
        filename = os.path.basename(urlparse(url).path)

        if not filename.lower().endswith(".pdf"):
            filename = "document.pdf"

        if self.state.file_exists(url):
            self.state.remove_queue(url)
            return "skipped"

        try:
            print(f"⬇️ Downloading: {filename} from {url}")
            local_path, file_hash = self.downloader.download(url, filename)

            with self._hash_lock:
                if file_hash in self.existing_hashes:
                    os.remove(local_path)
                    self.state.add_file(url, file_hash)
                    self.state.remove_queue(url)
                    return "duplicate"

                self.existing_hashes.add(file_hash)

            new_filename = self.downloader.rename_if_duplicate(
                filename, file_hash, self.existing_hashes
            )

            uploaded_path = self.uploader.upload(site, local_path, new_filename)

            self.state.add_file(url, file_hash)
            os.remove(local_path)
            self.state.remove_queue(url)

            print(f"✅ Uploaded: {uploaded_path}")
            return "success"

        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")
            return "failed"

    # ---------- Monitoring ----------
    def get_queue_size(self):
        return self.thread_queue.qsize()
