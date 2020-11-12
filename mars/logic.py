#!/usr/bin/env python3
"""
logic.py
Logic functions which allow the robot to perform tasks autonomously

Mechatronics 2
~ Callum Morrison, 2020
"""

import time

from mars import coords, logs, settings
from mars.comms import commands

log = logs.create_log(__name__)


class common:
    """
    Used for global parameters and shared functions.
    """
    pass
    # def __init__(self):
    #     engineer.next_task()


class engineer:
    """
    Used for functions and states specific to the Engineer.
    """

    def __init__(self):

        # General route the Engineer wishes to take:
        # - Start at launch pad
        # - Complete tasks in order: 1, 2, 3
        # - Return to launch pad
        self.desired_path = [2, 17, 9, 12, 2]

        # Index of the task which needs to be completed
        self.current_task = 0

        # Last known position in the compound
        self.current_marker = 0

    def next_task(self):
        """
        Aims to complete the next task in the task list
        """

        # 1. Determine route to get to next task
        self.current_marker = self.desired_path[self.current_task]
        target_marker = self.desired_path[self.current_task + 1]
        target_route = coords.route().pathfinder(self.current_marker, target_marker)

        reached_target = False

        while not reached_target:

            reached_marker = False

            while not reached_marker:
                # Save start time to synchronise framerate
                start_time = time.time()

                # Calculate distance to next marker in route
                magnitude, direction = coords.coords().calculate_vector(
                    "engineer", target_route[0])

                # If within target radius of target marker
                if magnitude < settings.MARKER_RADIUS:
                    log.debug("Engineer within target marker radius!")
                    log.debug("Moving to next marker...")

                    # Update current position
                    self.current_marker = target_route[0]

                    # Remove from route
                    target_route.pop(0)
                    reached_marker = True

                else:
                    # Calculate distance to alien
                    alien_distance, _ = coords.coords().calculate_vector(
                        "engineer", "alien")

                    # If within hearing distance, re-calculate route with alien avoidance
                    if alien_distance < settings.DETECTION_RADIUS:
                        log.debug("Engineer within hearing distance of alien!")
                        new_target_route = coords.route().pathfinder(
                            self.current_marker, target_marker, avoid=alien.current_marker)

                        # Check if no route has been found, if so throw a fit
                        if not new_target_route:
                            log.error(
                                f"The engineer can't find any route to it's target: {target_marker}!")
                            continue

                        # Check if new route is in the same direction, or a new direction
                        if target_route[1] == new_target_route[1]:
                            # Continue in same direction; remove the first element to prevent backgracking
                            new_target_route.pop(0)

                        target_route = new_target_route

                    else:
                        # Send a command to go to the first marker in the route
                        # commands.move("engineer", magnitude, direction)
                        pass

                # Wait until the next frame is required
                end_time = time.time()
                time_remain = start_time + 1 / settings.FRAMERATE - end_time

                if time_remain > 0:
                    time.sleep(time_remain)

            if not target_route:
                # Route is complete
                reached_target = True


class alien:
    """
    Used for functions and states specific to the Alien.
    """

    def __init__(self):
        self.current_marker = 99
