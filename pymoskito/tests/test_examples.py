import sys
import os
import unittest
import subprocess
import re


class TestExamples(unittest.TestCase):
    """ Test Suite for the included examples"""

    def test_ballbeam(self):
        self._test_example("ballbeam", debug=False)

    def test_balltube(self):
        self._test_example("balltube", debug=False)

    def test_simple_pendulum(self):
        self._test_example("simple_pendulum", debug=False)

    def test_pendulum(self):
        self._test_example("pendulum", debug=False)

    def test_car(self):
        self._test_example("car", debug=False)

    def test_tanksystem(self):
        self._test_example("tanksystem", debug=True)

    def _test_example(self, name: str, debug=False):
        """
        Run the given example while listening for errors on stdout

        Args:
            name(str): Module name of the Example to run
            debug: If True, display all output from stdout. Pretty handy when
                things take longer.

        Raises:
            failureException: If the output contains log entries that mention
                "- ERROR -".
        """
        print("Testing Example: {}".format(name))
        pattern = re.compile(r"(- ERROR -)")
        script = os.sep.join([os.path.dirname(__file__), "example_runner.py"])
        cmd = [sys.executable, script, name]

        with subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              bufsize=1,
                              universal_newlines=True) as proc:
            for line in proc.stdout:
                if debug:
                    print(line, end="")
                if pattern.search(line):
                    proc.kill()
                    self.fail(line)

        if proc.returncode != 0:
            raise self.failureException("Process terminated with: {}"
                                        "".format(proc.returncode))
