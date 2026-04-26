import json
import os
import threading


class StateManager:
    def __init__(self, site_name):
        # Thread lock for all state access
        self._lock = threading.Lock()

        # Create safe filename from site name
        safe_name = (site_name.replace("https://", "")
                     .replace("http://", "")
                     .replace("/", "")
                     .replace("www.", "")
                     )

        project_root = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(project_root, "state_manager")
        os.makedirs(base_dir, exist_ok=True)
        self.state_file = os.path.join(base_dir, f"{safe_name}.json")

        # Default state
        self.state = {
            "registry": {},  # {url: file_hash}
            "crawler": {
                "visited": [],
                "queue": []
            }
        }

        # Load existing state
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                self.state = json.load(f)

    # ---------- Registry ----------
    @property
    def registry(self):
        with self._lock:
            return dict(self.state["registry"])

    def add_file(self, url, file_hash):
        with self._lock:
            self.state["registry"][url] = file_hash
            self._save_locked()

    def file_exists(self, url):
        with self._lock:
            return url in self.state["registry"]

    # ---------- Crawler ----------
    @property
    def visited(self):
        with self._lock:
            return set(self.state["crawler"]["visited"])

    def add_visited(self, url):
        with self._lock:
            if url not in self.state["crawler"]["visited"]:
                self.state["crawler"]["visited"].append(url)
                self._save_locked()

    @property
    def queue_list(self):
        with self._lock:
            return list(self.state["crawler"]["queue"])

    def add_queue(self, url):
        with self._lock:
            if url not in self.state["crawler"]["queue"]:
                self.state["crawler"]["queue"].append(url)
                self._save_locked()

    def remove_queue(self, url):
        with self._lock:
            if url in self.state["crawler"]["queue"]:
                self.state["crawler"]["queue"].remove(url)
                self._save_locked()

    # ---------- Persistence ----------
    def save(self):
        with self._lock:
            self._save_locked()

    def _save_locked(self):
        """Save state to disk (lock must already be held)"""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
