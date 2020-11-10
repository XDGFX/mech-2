#!/usr/bin/env python3
"""
The main control file for all logic functions.
Mechatronics 2

Callum Morrison, 2020
"""

from mars import logs

log = logs.create_log(__name__)


class coords:
    def __init__(self):
        num_markers = 64

        # Array of all aruco codes available
        self.markers = [0] * num_markers

        # Corresponding aruco ids
        self.ids = {
            "engineer": 0,
            "alien": 1,
            "entrance": 2
        }

    def update(self, index, rvecs, tvecs):
        """
        Save a new position matrix to an aruco code id
        """
        index = index[0]

        self.markers[index] = {
            "tvecs": tvecs[0],
            "rvecs": rvecs[0]
        }

    def get_pos(self, entity):
        """
        Get the current position of the engineer or alien
        """
        try:
            return self.markers(self.ids[entity])
        except Exception as e:
            log.exception(e)
            return False
