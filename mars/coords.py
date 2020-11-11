#!/usr/bin/env python3
"""
coords.py
Responsible for handling positional data for the engineer, alien, and compound, as well as pathfinding algorithms.

Mechatronics 2
~ Callum Morrison, 2020
"""

import json
import math
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

            self.calculate_vector("engineer", "alien")

    def get_pos(self, entity):
        """
        Get the current position of an aruco marker
        """
        try:
            # Valid for aruco code ids or entity names
            if isinstance(entity, int):
                return self.markers[entity]
            else:
                return self.markers[self.ids[entity]]

        except Exception as e:
            log.exception(e)
            return False

    def calculate_vector(self, source, target):
        """
        Calculates the vector between two aruco markers.

        @returns:
        magnitude - Size of the vector
        direction - Angle of the vector in radians (CW)
        """

        # Get latest positions for both markers
        pos_source = self.get_pos(source)
        pos_target = self.get_pos(target)

        # Both markers need to be detected
        if not (pos_source and pos_target):
            log.error(
                "Vector calculation between two points failed because one or both points did not exist!")
            return

        # Calculate distance between markers
        magnitude = math.sqrt(
            (pos_target[0] - pos_source[0])**2 + (pos_target[1] - pos_source[1])**2)

        # Calculate direction to north by subtracting two angles
        direction = - pos_source[2]

        # Add extra totation to point towards the target
        direction -= math.atan((pos_target[0] - pos_source[0]) /
                               (pos_target[1] - pos_source[1]))

        log.debug(
            f"Vector {source} > {target}: Magnitude = {magnitude} | Direction = {direction}")

        return magnitude, direction


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
