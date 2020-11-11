#!/usr/bin/env python3
"""
coords.py
Responsible for handling positional data for the engineer, alien, and compound, as well as pathfinding algorithms.

Mechatronics 2
~ Callum Morrison, 2020
"""

import json
import time

from mars import logs, settings
from mars.webapp import ws_send

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

        # Initialise start time for datarate sync
        self.start_time = time.time()

    def update(self, index, tvecs, yaw):
        """
        Save a new position matrix to an aruco code id
        """
        index = index[0]

        # Assign markers in format [x_pos, y_pos, yaw]
        self.markers[index] = [tvecs[0][0], tvecs[0][1], yaw]

        # Only send updated marker positions at required polling interval
        end_time = time.time()
        time_remain = self.start_time + 1 / settings.DATARATE - end_time

        # Update markers on UI
        if time_remain < 0:
            ws_send("update_markers", json.dumps(self.markers))
            self.start_time = time.time()

    def get_pos(self, entity):
        """
        Get the current position of an aruco marker
        """
        try:
            return self.markers(self.ids[entity])
        except Exception as e:
            log.exception(e)
            return False


class route:
    """
    Storage of allowable paths that can be travelled.
    Stored in a two-layer list of the following format:

        [
            aruco0,   aruco0 = [aruco1]             (From aruco0 travel to aruco1 is allowed)
            aruco1,   aruco1 = [aruco0, aruco2]     (From )
            ...
            arucoN
        ]

    """
    allowed_routes = [
        [],  # Reserved for engineer
        [],  # Reserved for alien
        [3],  # 2 - Front door
    ]
