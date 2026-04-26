from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class WebCrawler:
    def __init__(self, state_manager, downloader, uploader, queue):
        self.state = state_manager
        self.downloader = downloader
        self.uploader = uploader
        self.queue = queue
        self.pages_crawled = 0
        self.pdfs_found = 0

    def crawl(self, start_url, allowed_domain):
        """Crawl website using queue instead of recursion"""
        # Use queue for pages to crawl instead of recursion
        url_queue = [start_url]

        while url_queue:
            url = url_queue.pop(0)

            if url in self.state.visited:
                continue

            self.state.add_visited(url)
            self.pages_crawled += 1

            # Print progress every 10 pages
            if self.pages_crawled % 10 == 0:
                print(f"📄 Crawled {self.pages_crawled} pages, found {self.pdfs_found} PDFs on {allowed_domain}")

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    continue

            except Exception as e:
                print(f"❌ Failed to crawl {url}: {e}")
                continue

            try:
                soup = BeautifulSoup(response.text, "html.parser")
            except Exception as e:
                print(f"❌ Failed to parse {url}: {e}")
                continue

            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(url, href)

                # Normalize URL
                parsed_url = urlparse(full_url)
                if not parsed_url.netloc and not parsed_url.scheme:
                    continue

                if full_url.lower().endswith(".pdf"):
                    self.pdfs_found += 1
                    print(f"📥 Found PDF ({self.pdfs_found}): {full_url}")
                    if full_url not in self.state.registry:
                        self.state.add_queue(full_url)
                        self.queue.add(full_url, start_url)  # Use original site URL
                    continue

                # Check if link is in the same domain
                if parsed_url.netloc == allowed_domain:
                    if full_url not in self.state.visited and full_url not in url_queue:
                        url_queue.append(full_url)

            # Remove from queue when page is crawled
            self.state.remove_queue(url)

        print(
            f"✅ Finished crawling domain: {allowed_domain} - {self.pages_crawled} pages, {self.pdfs_found} PDFs found")
