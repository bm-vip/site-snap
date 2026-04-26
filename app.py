import threading
import time
from urllib.parse import urlparse

from config import Config
from crawler import WebCrawler
from downloader import Downloader
from minio_client import MinioClient
from queue_manager import DownloadQueue
from state_manager import StateManager


def main():
    config = Config()
    uploader = MinioClient(
        config.minio_endpoint,
        config.minio_access_key,
        config.minio_secret_key,
        config.minio_bucket,
        config.minio_secure
    )

    # Create shared downloader
    downloader = Downloader()

    # List to track all queues and their threads
    site_threads = []

    for url in config.start_urls:
        print(f"🌐 Starting crawl for: {url}")

        # Create state manager for each site
        state_manager = StateManager(url)

        # Create queue for each site
        queue = DownloadQueue(downloader, uploader, state_manager)

        # Create crawler for each site
        crawler = WebCrawler(state_manager, downloader, uploader, queue)

        # Extract domain for allowed_domain
        domain = urlparse(url).netloc

        # Create and start thread for this site
        site_thread = threading.Thread(
            target=process_site,
            args=(crawler, url, domain, queue),
            name=f"Site-{domain}",
            daemon=False
        )
        site_thread.start()
        site_threads.append((site_thread, queue, domain))

    print("🚀 All crawlers started. Processing sites in parallel...")

    # Monitor progress and wait for completion
    monitor_progress(site_threads)

    print("✅ Completed all tasks")


def process_site(crawler, start_url, domain, queue):
    """
    Process a single site: crawl and download in parallel within the same thread
    """
    print(f"🔍 Starting to crawl: {start_url}")

    # Start crawling in a separate thread within this process
    crawl_thread = threading.Thread(
        target=crawler.crawl,
        args=(start_url, domain),
        name=f"Crawl-{domain}",
        daemon=False
    )
    crawl_thread.start()

    # Start downloading while crawling is in progress
    print(f"📥 Starting download queue for: {domain}")
    queue.run_continuous()

    # Wait for crawling to complete
    crawl_thread.join()

    # Stop continuous processing after crawling is done
    queue.stop_continuous()
    print(f"✅ Finished processing site: {domain}")


def monitor_progress(site_threads):
    """
    Monitor progress of all site threads and provide status updates
    """
    active_threads = len(site_threads)

    while active_threads > 0:
        active_threads = 0
        status_report = []

        for thread, queue, domain in site_threads:
            if thread.is_alive():
                active_threads += 1
                queue_size = queue.get_queue_size()
                status_report.append(f"{domain}: {queue_size} in queue")
            else:
                status_report.append(f"{domain}: COMPLETED")

        # Print progress every 10 seconds
        if active_threads > 0:
            print(f"📊 Progress: {active_threads} sites active | {', '.join(status_report)}")
            time.sleep(10)
        else:
            break

    print("🎉 All sites processed successfully!")


if __name__ == "__main__":
    main()