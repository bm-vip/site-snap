# Site Crawler & Downloader

Crawls and fetches files, then stores them in MinIO

An automated Python application that crawls websites, discovers downloadable PDF documents, downloads them, deduplicates them using SHA256 hashing, and uploads them to MinIO object storage — all with full resume capability for both crawling and downloading.

## Overview

This application automatically:
- Crawls one or multiple websites recursively
- Discovers PDF files from any depth of the website
- Downloads PDF files while preventing duplicates
- Renames files when duplicates exist
- Uploads files into MinIO object storage under per-domain folders
- Maintains a unified state file to resume crawling and downloading
- Utilizes a threaded queue for fast parallel downloads
- Cleans temporary files after uploading

## Features

- **Multi-Site Crawling**: Multi-threaded downloads with resume capability
- **Deep Recursive Crawler**: SHA256 checksum verification and file size validation
- **PDF Auto-Detection**: Handles multiple versions of data for the same date
- **Download Deduplication**: Full pipeline from download to storage
- **Smart Rename**: Skips already processed files
- **MinIO Upload**: Real-time download progress and status updates
- **Parallel Queue System**: Real-time download progress and status updates
- **Global Resume System:**:
    - Crawler resumes from where it left off
    - Download queue resumes remaining tasks
    - Registry ensures no duplicate downloads
- **Single State File:** All registry and crawler state stored in one JSON
- **Clean Temp Handling:** Downloads each file to /tmp, uploads, then removes

## Prerequisites

- Python 3.8+
- MinIO instance (or compatible S3 storage)
- Internet connection for data source access

## Installation

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
       git clone https://github.com/bm-vip/site-snap
       cd site-snap
   ```

2. **Build the Docker image**:

     ```bash
        docker build -t site-snap .
     ```
3. **Run the container**:

     ```bash
        docker run -it --rm site-snap
     ```

## Manual Installation
1. **Create virtual environment**:
    ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
2.  **Install dependencies**:
    ```bash
        pip install -r requirements.txt
     ```
3.  **Run the application**:
    ```bash
        python app.py
     ```

## ⚙️ Configuration

### Environment Variables

Configure the application using these environment variables:

| Variable           | Description                       | Default                     |
|--------------------|-----------------------------------|-----------------------------|
| `START_URLS`       | Comma-separated list of root URLs | `https://example.com,a.com`        |
| `MINIO_ENDPOINT`   | MinIO server endpoint             | `localhost:9000`        |
| `MINIO_ACCESS_KEY` | MinIO access key                  | `minioadmin`                |
| `MINIO_SECRET_KEY` | MinIO secret key                  | `minioadmin`         |
| `MINIO_BUCKET`     | Target bucket name                | `site-snap`   |
| `MINIO_SECURE`     | Use HTTPS connection              | `true`                      |

---

### Example Docker Run with Custom Configuration

```bash
   docker run -it --rm \
  -e START_URLS="https://www.nv-online.de,https://example.org" \
  -e MINIO_ENDPOINT=minio \
  -e MINIO_ACCESS_KEY=your-access-key \
  -e MINIO_SECRET_KEY=your-secret-key \
  -e MINIO_BUCKET=site-snap \
  ste-snap
 ```
### Project Structure

```angular2html
crawler/
├── app.py               # Main application entry point
├── crawler.py           # Core recursive crawler engine
├── downloader.py        # Handles file downloading + hashing + rename
├── queue_manager.py     # Multi-threaded task queue manager
├── state_manager.py     # Unified state registry (crawler + downloads)
├── minio_client.py      # MinIO uploader component
├── utils.py             # Shared utilities (hashing, URL helpers)
├── requirements.txt     # Dependencies
└── README.md            # This file

```
### How it works
1. Startup: Loads state.json (or creates empty one)
2. URL Bootstrapping: Inserts all START_URLS into crawler queue
3. Recursive Crawling:
   - Visits each page once
   - Extracts links
   - Detects PDF links
   - Saves discovered PDFs into download queue

4. Queue Processing (Parallel):
   - Downloads file → computes SHA256
   - Checks registry for duplicates
   - Renames file if needed

5. Upload to MinIO:
   - Files stored under:
     `domain.com/filename.pdf`

6. State Persistence:
   - Visited pages
   - Pending crawl queue
   - Pending download tasks
   - Registry of downloaded files

7. Cleanup:
   - Temporary files removed

Everything is fully resumable upon restart. 

### Folder Structure in MinIO
No nested path reconstruction.<br>
All PDFs for each website domain are stored in a single folder:
```angular2html
website-documents/
├── nv-online.de/
│   ├── file1.pdf
│   ├── file1_1.pdf
│   ├── file2.pdf
│   └── ...
├── example.org/
│   ├── doc.pdf
│   └── doc_1.pdf

```

### Monitoring
Detailed logging with clean indicators:
* 🌐 Crawling page
* 🔍 Extracted link
* 📄 Found PDF
* ➕ Added to queue
* 🚀 Download started
* ⬇️ Download progress
* 🔐 SHA256 computed
* 🔁 Duplicate detected → renamed
* 📤 Uploaded to MinIO
* 🧹 Temporary file removed
* 💾 State saved
* ❌ Error processing

### Error Handling
* Auto-retry failed downloads
* Skips already downloaded PDFs
* Avoids revisiting pages
* Cleans partial files after failure
* Ensures state.json is always consistent
* Hash-based detection of truly duplicate files
* Robust queue system prevents missing tasks
* Graceful shutdown with resume support
