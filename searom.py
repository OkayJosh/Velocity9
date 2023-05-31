import concurrent.futures
import gzip
import sys
import urllib.request
import os
from urllib.parse import unquote

from tqdm import tqdm
from multiprocessing.pool import ThreadPool
import time


from settings import configure_logging, SEAROM, DOWNLOAD_AT
from daemon import Daemon


LOG = configure_logging()


class Downloader(Daemon):
    def __init__(self, pidfile: str, url: str):
        super().__init__(pidfile)
        self.max_length = SEAROM.get('MAXIMUM_LENGTH', 10)
        self.failed_chunks = []
        self.downloaded_chunks = []
        self.retries = SEAROM.get('MAXIMUM_RETRIES', 10)
        self.num_chunks = SEAROM.get('MAXIMUM_CHUNKS', 10)
        self.url = url
        self.save_directory = DOWNLOAD_AT

    def run(self):
        self.download_url(self.url, self.save_directory)

    def download_chunk(self, chunk_info):
        chunk_url, chunk_save_path, range_header = chunk_info
        retries = 10  # Number of times to retry the download
        if (chunk_url, chunk_save_path, range_header) not in self.downloaded_chunks:
            for _ in range(retries):
                try:
                    if os.path.exists(chunk_save_path):
                        resume_header = f"bytes={os.path.getsize(chunk_save_path)}-"
                        range_header = resume_header + range_header

                    req = urllib.request.Request(chunk_url, headers={"Range": range_header})

                    # Enable compression
                    req.add_header("Accept-Encoding", "gzip, deflate")

                    response = urllib.request.urlopen(req)

                    # Check if the response is compressed
                    if response.info().get("Content-Encoding") == "gzip":
                        response = gzip.GzipFile(fileobj=response)

                    with open(chunk_save_path, 'wb') as file:
                        file.write(response.read())
                        self.downloaded_chunks.append((chunk_url, chunk_save_path, range_header))
                    return  # Download successful, exit the function
                except Exception as e:
                    LOG(f"An error occurred during the download: {e}")
                    LOG("Retrying download...")
                    time.sleep(1)  # Wait for 1 second before retrying

            LOG(f"Download failed for {chunk_save_path}")
            LOG(f"Logging failed download with path {chunk_save_path} and range header {range_header}")
            self.failed_chunks.append((chunk_url, chunk_save_path, range_header))
        else:
            LOG(f"{chunk_save_path} has already been downloaded")
            self.failed_chunks.remove((chunk_url, chunk_save_path, range_header))

    def download_url(self, url, save_directory):
        try:
            # Extract the file name from the URL or response headers
            file_name = os.path.basename(url)
            file_name = self.truncate_filename(file_name,
                                               max_length=self.max_length)  # Set the maximum length as desired
            response = urllib.request.urlopen(url)
            headers = dict(response.headers)
            if 'Content-Disposition' in headers:
                disposition = headers['Content-Disposition']
                file_name = disposition.split('filename=')[1].strip('"\'')
                file_name = self.truncate_filename(file_name,
                                                   max_length=self.max_length)  # Set the maximum length as desired

            # Generate a unique file name based on the current timestamp
            save_path = os.path.join(save_directory, file_name)

            # Get the file size
            file_size = int(headers["Content-Length"])

            # Define the number of chunks to download and chunk size
            # num_chunks = 100  # Adjust this value to control the number of concurrent downloads
            chunk_size = file_size // self.num_chunks

            # Generate chunk URLs and save paths
            chunks = []
            for i in range(self.num_chunks):
                start_byte = i * chunk_size
                end_byte = start_byte + chunk_size - 1 if i < self.num_chunks - 1 else ""
                range_header = f"bytes={start_byte}-{end_byte}"
                chunk_url = url if isinstance(url, str) else url.decode()
                chunk_save_path = f"{save_path}.part{i}"
                chunks.append((chunk_url, chunk_save_path, range_header))

            # Perform concurrent downloads with progress indicator
            with tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024, miniters=1, desc=file_name) as t:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_chunks) as executor:
                    download_futures = [executor.submit(self.download_chunk, chunk_info) for chunk_info in chunks]
                    for future in concurrent.futures.as_completed(download_futures):
                        t.update(chunk_size)

            # Retry failed chunks
            allowed_retries = 0
            while self.failed_chunks and allowed_retries < self.retries:
                LOG("Retrying failed chunks...")
                failed_chunks_copy = self.failed_chunks.copy()
                self.failed_chunks = []

                with tqdm(total=len(failed_chunks_copy), unit="chunk", desc="Retrying") as t:
                    with ThreadPool(len(failed_chunks_copy)) as pool:
                        for _ in pool.imap_unordered(self.download_chunk, failed_chunks_copy):
                            t.update(1)

            # Merge downloaded chunks into a single file
            with open(save_path, "wb") as outfile:
                for i in range(self.num_chunks):
                    chunk_save_path = f"{save_path}.part{i}"
                    with open(chunk_save_path, "rb") as infile:
                        outfile.write(infile.read())

                    # Delete chunk file after merging
                    os.remove(chunk_save_path)

            LOG("Download completed successfully!")
        except Exception as e:
            LOG(f"An error occurred during the download: {e}")

    def truncate_filename(self, filename, max_length):
        filename = unquote(filename.split("?filename=")[-1])
        if len(filename) > max_length:
            basename, extension = os.path.splitext(filename)
            truncated_name = basename[:max_length - len(extension)] + extension
            return truncated_name
        return filename

