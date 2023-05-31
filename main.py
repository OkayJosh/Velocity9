import os
import sys
from searom import Downloader

if __name__ == "__main__":
    # Get the home directory
    home_dir = os.path.expanduser("~")
    # Construct the pidfile path
    pidfile = os.path.join(home_dir, "speadsearom.pid")

    if len(sys.argv) == 3 and sys.argv[1] == "start":
        url = sys.argv[2]

        downloader = Downloader(pidfile, url)
        downloader.start()
        sys.exit(0)
    elif len(sys.argv) == 2 and sys.argv[1] == "stop":
        downloader = Downloader(pidfile, "")
        downloader.stop()
    else:
        print("Usage: python main.py start <url>\n"
              "python main.py stop")
        sys.exit(2)
