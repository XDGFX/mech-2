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
from copy import deepcopy

import redis

from mars import logs, settings
from mars.comms import commands
from mars.logic import update_ui

log = logs.create_log(__name__)

r = redis.Redis(host='localhost', port=6379,
                db=0, decode_responses=True)


class coords:
    def __init__(self):
        # Initialise markers database
        # self.db_file = os.path.join("mars", "cam_data", "markers.db")
        num_markers = 21

        # with sqlite3.connect(self.db_file) as conn:
        #     cursor = conn.cursor()

        #     query = "CREATE TABLE IF NOT EXISTS markers (marker INTEGER PRIMARY KEY, x REAL, y REAL, a REAL)"
        #     cursor.execute(query)

        #     # --- This was removed because it would clear the database any time
        #     # --- a new module tried to access the database
        #     # # Array of all aruco codes available
        #     # markers = [(i, 0, 0, 0) for i in range(num_markers)]

        #     # query = "REPLACE INTO markers (marker, x, y, a) VALUES(?, ?, ?, ?)"
        #     # cursor.executemany(query, markers)

        #     conn.commit()

        # Initialise markers variable for UI
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
        index = int(index[0])

        old_marker = self.get_pos(index)

        # Smooth changes in marker position
        if old_marker:
            x_pos = old_marker[0] * (1 - settings.MARKER_SMOOTHING) + \
                tvecs[0][0] * settings.MARKER_SMOOTHING
            y_pos = old_marker[1] * (1 - settings.MARKER_SMOOTHING) + \
                tvecs[0][1] * settings.MARKER_SMOOTHING
        else:
            x_pos = tvecs[0][0]
            y_pos = tvecs[0][1]

        # Don't smooth if angle switches sign from previous (loop round 180 to -180)
        try:
            sign_change = (yaw < 0) != (old_marker[2] < 0)
        except TypeError:
            sign_change = True

        if not sign_change:
            yaw = old_marker[2] * (1 - settings.MARKER_SMOOTHING) + \
                yaw * settings.MARKER_SMOOTHING

        # Assign markers in format [x_pos, y_pos, yaw]
        try:
            self.markers[index] = [
                round(x_pos, 4),
                round(y_pos, 4),
                round(yaw, 4)]
        except IndexError:
            # The camera has accidentally detected a marker we're not using, discard
            return

        # with redis.Redis(host='localhost', port=6379, db=0, decode_responses=True) as r:
        r.set(index, json.dumps([x_pos, y_pos, yaw]))

        # with sqlite3.connect(self.db_file) as conn:
        #     cursor = conn.cursor()

        #     query = "REPLACE INTO markers (marker, x, y, a) VALUES (?, ?, ?, ?)"
        #     cursor.execute(query, (index, x_pos, y_pos, yaw))

        #     conn.commit()

        # Only send updated marker positions at required polling interval
        end_time = time.time()
        time_remain = self.start_time + 1 / settings.DATARATE - end_time

        # Update markers on UI
        if time_remain < 0:
            from mars.webapp import ws_send
            ws_send("update_markers", json.dumps(self.markers))
            self.start_time = time.time()

    def get_pos(self, entity):
        """
        Get the current position of an aruco marker
        """
        try:
            # Valid for aruco code ids or entity names
            if isinstance(entity, int):
                index = entity
            else:
                index = self.ids[entity]

            # with sqlite3.connect(self.db_file) as conn:
            #     cursor = conn.cursor()

            #     query = "SELECT x, y, a FROM markers WHERE marker = ?"
            #     cursor.execute(query, (index,))

            #     rows = cursor.fetchone()

            try:
                marker = json.loads(r.get(index))
            except TypeError:
                log.warning(f"Invalid marker position for index: {index}!")
                return [-999, -999, -999]

            return marker

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
        direction = -pos_source[2]

        delta_x = pos_target[0] - pos_source[0]
        delta_y = pos_source[1] - pos_target[1]

        # Add extra rotation to point towards the target
        try:
            direction += math.atan(delta_x / delta_y)
        except ZeroDivisionError:
            direction += math.pi / 2

        # If delta_y is positive, angle correction by adding pi
        if delta_y > 0:
            direction -= math.pi

        # Manual angle correction
        direction = (math.pi - direction) % (2 * math.pi)

        # Convert to +/- pi
        if direction > math.pi:
            direction = -2 * math.pi + direction

        log.debug(
            f"Vector {source} > {target}: Magnitude = {magnitude:.2f} | Direction = {direction / math.pi * 180:.2f}")

        return magnitude, direction


class route:
    """
    Storage of allowable paths that can be travelled.
    Stored in a two-layer list of the following format:

        [
            aruco0,   aruco0 = [aruco1]             (From aruco0 travel to aruco1 is allowed)
            aruco1,   aruco1 = [aruco0, aruco2]     (From aruco 1, travel to aruco 0 or 2)
            ...
            arucoN
        ]

    """

    def __init__(self):
        # Routes allowed for the engineer
        self.allowed_routes = [
            [],                 # Reserved for engineer
            [],                 # Reserved for alien
            [4, 15],            # 2 - Launch Pad
            [],                 # 3 - Unused
            [2, 5],             # 4
            [4, 6],             # 5
            [5, 7],             # 6
            [6, 8, 17],         # 7 - Door B
            [7, 9, 18],         # 8 - Door A
            [8, 10],            # 9 - Door A; Alien Start; Second Task
            [9, 11],            # 10
            [10, 12, 13],       # 11
            [11, 13, 20],       # 12 - Third Task; Door D
            [11, 12, 14, 19],   # 13 - Door C
            [13, 15, 16],       # 14
            [2, 14, 20],        # 15
            [14, 17],           # 16
            [7, 16],            # 17 - First Task; Door B
            [8, 19],            # 18
            [13, 18],           # 19 - Door C
            [12, 15],           # 20 - Door D
        ]

        # Markers which require a check for an open door
        self.markers_doors = [
            [8, 9],     # Door 1 / A
            [7, 17],    # Door 2 / B
            [19, 13],   # Door 3 / C
            [20, 12]    # Door 4 / D
        ]

        # Update shortcuts for alien
        self.allowed_routes_alien = deepcopy(self.allowed_routes)

        self.allowed_routes_alien[4].append(17)
        self.allowed_routes_alien[17].append(4)

        self.allowed_routes_alien[17].append(18)
        self.allowed_routes_alien[18].append(17)

        self.allowed_routes_alien[18].append(10)
        self.allowed_routes_alien[10].append(18)

        self.allowed_routes_alien[16].append(2)
        self.allowed_routes_alien[2].append(16)

        # self.weights = [
        #     0,  # Reserved for engineer
        #     0,  # Reserved for alien
        #     1,  # 2 - Front door
        # ]

    def initialise_doors(self):
        # Current state of all doors, all open to start
        r.set("doors_state", json.dumps([
            True,       # Door 1 / A
            True,       # Door 2 / B
            True,       # Door 3 / C
            True        # Door 4 / D
        ]))

        self.doors(0, True)
        self.doors(1, True)
        self.doors(2, True)
        self.doors(3, True)

        update_ui()

        # Initialise comms object
        self.cmd = commands()
        self.cmd.doors_send()

    def doors(self, index, state):
        """
        Opens or closes a door identified by `index`.
        `state` is True for open and False for closed.
        """
        doors_state = json.loads(r.get("doors_state"))
        doors_state[index] = state
        r.set("doors_state", json.dumps(doors_state))

        log.info(f"Command: {state} send to door index: {index}")

        # self.cmd.door(index, state)

        update_ui()

    def pathfinder(self, start, finish, shortcuts=False, avoid=None):
        """
        Computes fastest path between two points, with an optional avoidance parameter.
        Will not pass over the same point twice.
        `start`, `finish`, and `avoid`, should all be aruco code integers.
        `shortcuts` are True for Alien, and False for Engineer.

        @return:
        `route`: A list of codes to travel through to the destination.
        """

        # Initialise all routes
        routes = []
        routes_old = []
        solution_found = False

        # Adjust routes according to shortcuts
        if shortcuts:
            allowed_routes = deepcopy(self.allowed_routes_alien)
        else:
            allowed_routes = deepcopy(self.allowed_routes)

        # Check if doors are locked and adjust route if required
        doors_state = json.loads(r.get("doors_state"))
        for index in range(4):

            # Check if door is closed
            if doors_state[index]:
                continue

            # Only adjust if start point next to a door
            if start in self.markers_doors[index]:

                # Remove route through the door
                for code in self.markers_doors[index]:
                    allowed_routes[code] = [
                        x for x in allowed_routes[code] if x not in self.markers_doors[index]]

        # Loop over all possible next positions from the starting position
        for next_point in allowed_routes[start]:
            if next_point != avoid:
                routes.append(
                    [start, next_point]
                )

        # Keep looking while new routes are being generated
        while routes and not solution_found:
            routes_old = routes
            routes = []

            # Loop over all current routes
            for route in routes_old:
                last_point = route[-1]

                # Append to routes if finish reached
                if last_point == finish:
                    routes.append(route)
                    solution_found = True
                    break

                # Loop over possible routes from here
                for next_point in allowed_routes[last_point]:

                    # Only update route if not already traversed through points
                    if next_point not in [*route, avoid]:

                        # Add new route to existing routes
                        routes.append([*route, next_point])

        # Remove routes which don't end at the finish
        routes = [route for route in routes_old if route[-1] == finish]

        # Rank remaining routes by length
        if routes:
            best_route = min(routes, key=len)

            return best_route

        # No route was found
        log.error(f"No route found between {start} and {finish}")
        return False
