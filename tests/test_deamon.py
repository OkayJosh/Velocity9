import unittest
from unittest import mock
import os

from daemon import Daemon


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.pidfile = "/tmp/daemon.pid"
        self.daemon = Daemon(self.pidfile)

    def tearDown(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def test_daemonize(self):
        with mock.patch("os.fork") as mock_fork, \
                mock.patch("os.chdir") as mock_chdir, \
                mock.patch("os.setsid") as mock_setsid, \
                mock.patch("os.umask") as mock_umask, \
                mock.patch("os.open") as mock_open, \
                mock.patch("sys.stdin") as mock_stdin, \
                mock.patch("sys.stdout") as mock_stdout, \
                mock.patch("sys.stderr") as mock_stderr, \
                mock.patch("atexit.register") as mock_register, \
                mock.patch("os.path.exists") as mock_exists, \
                mock.patch("os.remove") as mock_remove:
            mock_fork.return_value = 0
            mock_exists.return_value = False

            self.daemon.daemonize()

            mock_fork.assert_called()
            mock_chdir.assert_called_with("/")
            mock_setsid.assert_called()
            mock_umask.assert_called_with(0)
            mock_stdin.fileno.assert_called()
            mock_stdout.fileno.assert_called()
            mock_stderr.fileno.assert_called()
            mock_register.assert_called_with(self.daemon._remove_pidfile)

    def test__remove_pidfile(self):
        with mock.patch("os.path.exists") as mock_exists, \
                mock.patch("os.remove") as mock_remove:
            mock_exists.return_value = True

            self.daemon._remove_pidfile()

            mock_exists.assert_called_with(self.pidfile)
            mock_remove.assert_called_with(self.pidfile)

    def test_start(self):
        with mock.patch("daemon.Daemon.is_process_running") as mock_is_process_running, \
                mock.patch("daemon.Daemon.daemonize") as mock_daemonize, \
                mock.patch("daemon.Daemon.run") as mock_run, \
                mock.patch("sys.exit") as mock_exit:
            mock_is_process_running.return_value = False

            self.daemon.start()

            mock_is_process_running.assert_called()
            mock_daemonize.assert_called()
            mock_run.assert_called()

    def test_restart(self):
        with mock.patch.object(Daemon, "stop") as mock_stop, \
                mock.patch.object(Daemon, "start") as mock_start:
            self.daemon.restart()

            mock_stop.assert_called()
            mock_start.assert_called()

