"""Shared logger module."""
import os
import sys

VERBOSE = os.environ.get("LOG_LEVEL") == "debug"


class Logger:
    def debug(self, *args):
        if VERBOSE:
            sys.stderr.write("[DEBUG] " + " ".join(str(a) for a in args) + "\n")

    def info(self, *args):
        sys.stderr.write("[INFO]  " + " ".join(str(a) for a in args) + "\n")

    def error(self, *args):
        sys.stderr.write("[ERROR] " + " ".join(str(a) for a in args) + "\n")


logger = Logger()
