import logging
import os

BASE_DIR = os.path.expanduser("~")
DOWNLOAD_AT = os.path.join(BASE_DIR, "Downloads")

# Configure Searom
SEAROM = {
    'MAXIMUM_RETRIES': 10,
    'MAXIMUM_CHUNK': 10,
    'MAXIMUM_LENGTH': 50
}


def configure_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.DEBUG,  # Set the desired log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='velocity9.log',  # Specify the log file name
        filemode='a'  # Set the file mode ('w' for write mode)
    )
    console_handler = logging.StreamHandler()  # Add a console handler to display logs on the console
    console_handler.setLevel(logging.DEBUG)  # Set the log level for console output
    formatter = logging.Formatter('%(levelname)s::%(asctime)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)
    return logging
