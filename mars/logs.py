#!/usr/bin/env python3

"""
logs
The default logging module for ultrasonics, which should be used for logging consistency.
XDGFX, 2020
"""

import logging

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38m"
    blue = "\x1b[96m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;7mm"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def create_log(name):
    # Create logger
    log = logging.getLogger(name)

    log.setLevel(logging.DEBUG)

    # Add streamhandler to logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Apply log formatting
    ch.setFormatter(CustomFormatter())

    log.addHandler(ch)
    return log
