import unittest
import os
import zlib
import urllib.error
from unittest import mock

from searom import Downloader


class DownloaderTestCase(unittest.TestCase):
    def setUp(self):
        # Set up test data
        self.url = "https://example.com/file.txt"
        self.save_directory = "./test_dir"

        home_dir = os.path.expanduser("~")
        # Construct the pidfile path
        self.pidfile = os.path.join(home_dir, "speadsearom.pid")
        # Create an instance of the Downloader class
        self.downloader = Downloader(self.pidfile, self.url)

        self.create_chunk_part_file(filename='file.txt', chunks=self.downloader.num_chunks)

    def tearDown(self):
        # Clean up test data
        if os.path.exists(self.save_directory):
            # Remove files within the directory
            for root, dirs, files in os.walk(self.save_directory, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

            # Remove the directory
            os.rmdir(self.save_directory)

    def test_download_url(self):
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            # Set up mock response
            mock_response = mock.Mock()
            mock_response.headers = {
                "Content-Disposition": 'attachment; filename="file.txt"',
                "Content-Length": '0',
            }
            mock_response.read.return_value = b"Mock file content"
            mock_urlopen.return_value = mock_response
            self.create_chunk_part_file(filename="file.txt", chunks=self.downloader.num_chunks)
            # Download the file
            self.downloader.download_url(self.url, self.save_directory)

        # Assert that the file is downloaded and exists in the save directory
            file_path = os.path.join(self.save_directory, "file.txt")
            self.assertTrue(os.path.exists(file_path))

    def test_download_url_for_encoded_content(self):
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            # Set up mock response
            mock_response = mock.Mock()
            mock_response.headers = {
                "Content-Disposition": 'attachment; filename="file.txt"',
                "Content-Length": '0',
                "Content-Encoding": "gzip",  # Set the content encoding to gzip
            }
            mock_response.read.return_value = zlib.compress(b"Mock file content")  # Compress the content
            mock_urlopen.return_value = mock_response
            self.create_chunk_part_file(filename="file.txt", chunks=self.downloader.num_chunks)
            # Download the file
            self.downloader.download_url(self.url, self.save_directory)

            # Assert that the file is downloaded and exists in the save directory
            file_path = os.path.join(self.save_directory, "file.txt")
            self.assertTrue(os.path.exists(file_path))

    def test_download_url_with_error_104(self):
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            # Set up mock response for Error 104
            mock_urlopen.side_effect = urllib.error.URLError(reason="Error 104: Connection reset by peer")

            # Download the file
            self.downloader.download_url(self.url, self.save_directory)

        # Assert that the file is not downloaded and does not exist in the save directory
        file_path = os.path.join(self.save_directory, "file.txt")
        self.assertFalse(os.path.exists(file_path))

    def test_truncate_filename(self):
        # Test truncation of a long filename
        long_filename = "very_long_filename_that_exceeds_the_maximum_length.txt"
        truncated_name = self.downloader.truncate_filename(long_filename, max_length=20)
        expected_name = "very_long_filena.txt"
        self.assertEqual(truncated_name, expected_name)

    def create_chunk_part_file(self, filename, chunks):
        chunk_size = 10/chunks
        # Create the parent directory if it doesn't exist
        os.makedirs(self.save_directory, exist_ok=True)
        save_path = os.path.join(self.save_directory, filename)
        for i in range(chunks):
            start_byte = i * chunk_size
            end_byte = start_byte + chunk_size - 1 if i < chunks - 1 else ""
            # range_header = f"bytes={start_byte}-{end_byte}"
            # chunk_url = self.url if isinstance(self.url, str) else self.url.decode()
            chunk_save_path = f"{save_path}.part{i}"
            with open(chunk_save_path, "w") as file:
                # file.write("This is a sample file.")
                pass


