import os
import sys
import atexit

from settings import configure_logging

LOG = configure_logging()


class Daemon:
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.pidfile = os.path.expanduser(pidfile)  # Use the user's home directory for the PID file
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def daemonize(self):
        try:
            # Fork the current process
            pid = os.fork()

            if pid > 0:
                # Exit the parent process
                sys.exit(0)

        except OSError as e:
            LOG.INFO(f"Failed to fork process: {e}\n")
            sys.exit(1)

        # Change the working directory to root
        os.chdir("/")
        # Detach from the parent environment
        os.setsid()
        # Set the file permissions
        os.umask(0)

        try:
            # Fork again to prevent the process from acquiring a controlling terminal
            pid = os.fork()

            if pid > 0:
                # Write the child process PID to the PID file
                with open(self.pidfile, 'w') as f:
                    f.write(str(pid))
                sys.exit(0)

        except OSError as e:
            LOG.INFO(f"Failed to fork process: {e}\n")
            sys.exit(1)

        # Redirect standard file descriptors to devnull or specified files
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Register the exit function to remove the PID file
        atexit.register(self._remove_pidfile)

    def _remove_pidfile(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        # Check if the process is already running
        if self.is_process_running():
            LOG.INFO("Process is already running.")
            sys.exit(1)

        # Start the daemonization process
        self.daemonize()

        # Perform any additional setup or initialization here

        # Execute the daemon main function
        self.run()

    def stop(self):
        # Check if the process is not running
        if not self.is_process_running():
            LOG("Process is not running.")
            sys.exit(1)

        # Get the PID from the PID file
        with open(self.pidfile, 'r') as f:
            pid = int(f.read().strip())

        try:
            # Terminate the process
            os.kill(pid, 15)
        except OSError as e:
            LOG.INFO(f"Failed to stop process: {e}")
            sys.exit(1)

        # Remove the PID file
        self._remove_pidfile()

    def restart(self):
        # Stop the process
        self.stop()
        # Start the process
        self.start()

    def is_process_running(self):
        if os.path.exists(self.pidfile):
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            return os.path.exists(f"/proc/{pid}")
        return False

    def run(self):
        # Override this method with the daemon's main functionality
        # The daemon's main code goes here
        pass
